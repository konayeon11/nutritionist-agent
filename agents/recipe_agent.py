# agents/recipe_agent.py
"""
Service-friendly RecipeAgent (GPT-only, Marketing Copy + Clean Output)

요청 반영:
- 🔥 '한 줄 요약'을 사용자 프로필(식단/선호/시간/건강문맥/인벤토리)을 기반으로
  마케팅 카피톤으로 생성하여 카드 최상단에 표시
- 🧾 cost_tier, co2_footprint_note 완전 제거(모델 스키마/출력/카드 모두)
- ✅ 신뢰 출처 URL(있으면) 포함, 모든 텍스트 한국어
- 🧠 풍부한 정보 유지: 영양, 알레르겐, 장비, 대체재, 보관/재가열, 팁, 경고 등
- 🧩 인벤토리 교집합(uses) + STOPWORDS 제외 누락(missing) 계산
- 🔒 품질 필터: 인벤토리 최소 1개 일치 & 누락 ≤ max_missing
- 🏁 정렬: 누락 0 → 누락 적음 → 매칭 많음 → 점수

의존성: openai, pydantic
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field
import os, re, json, unicodedata, logging, hashlib

# ------------------- 로깅 -------------------
logger = logging.getLogger("recipe_agent")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# ------------------- 정규화/동의어/필터 -------------------
# 기본 조미료/기본재료는 missing에서 제외 (서비스 UX)
STOPWORDS = {
    "약간","적당량","조금","소금","후추","식용유","물","참기름","설탕","간장","식초","다진마늘","다시다","치킨스톡"
}
SYNONYM_MAP = {
    "egg":{"계란","달걀"},
    "spring_onion":{"대파","파","쪽파","실파"},
    "pork":{"돼지 고기","돼지고기"},
    "beef":{"소 고기","소고기"},
    "tofu":{"두부"},
    "garlic":{"마늘"},
    "onion":{"양파"},
    "scallion":{"대파","파","쪽파"},
    "kimchi":{"김치"},
    "soy_sauce":{"간장"},
    "sesame_oil":{"참기름"},
}

def _normalize(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKC", str(s).strip().lower())
    s = re.sub(r"\s+", " ", s)
    return s

def _expand_synonyms(token: str) -> set[str]:
    token = _normalize(token)
    ex = {token}
    for _, syns in SYNONYM_MAP.items():
        if token in syns:
            ex |= set(_normalize(x) for x in syns)
    return ex

def _stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((_normalize(p) + "|").encode("utf-8"))
    return h.hexdigest()[:16]

# ------------------- 데이터 모델 -------------------
class SourceModel(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None

class NutritionModel(BaseModel):
    calories_kcal: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    sodium_mg: Optional[int] = None

class SuitabilityModel(BaseModel):
    summary: Optional[str] = None
    health: Optional[str] = None
    inventory: Optional[str] = None
    time: Optional[str] = None
    occasion: Optional[str] = None
    skill: Optional[str] = None
    tips: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

class RecipeItem(BaseModel):
    # LLM이 반환해야 하는 최소 필드
    title: str                                    # 한국어 제목
    ingredients: List[str]
    steps: List[str]
    time_minutes: Optional[int] = None
    difficulty: Optional[str] = None              # 쉬움/보통/어려움
    tags: Optional[List[str]] = None
    servings: Optional[int] = None
    time_breakdown: Optional[Dict[str,int]] = None  # {"prep":10,"cook":15,"total":25}

    # 추가 메타
    source: Optional[SourceModel] = None
    nutrition: Optional[NutritionModel] = None
    allergens: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    substitutions: Optional[Dict[str, List[str]]] = None
    storage: Optional[str] = None
    reheat: Optional[str] = None
    suitability: Optional[SuitabilityModel] = None

@dataclass
class _Candidate:
    rec: RecipeItem
    score: float
    missing_count: int
    matched_count: int
    uses: List[str]
    missing: List[str]

# ------------------- 매칭/스코어링 -------------------
def _contains_allergen(ingredients: List[str], allergies: List[str]) -> bool:
    if not allergies: return False
    ing_set = {_normalize(x) for x in ingredients}
    for a in allergies:
        a_n = _normalize(a)
        for token in ing_set:
            if a_n in _expand_synonyms(token) or token in _expand_synonyms(a_n):
                return True
    return False

def _tokenize_ings(ings: List[str]) -> List[str]:
    out = []
    for raw in ings:
        if not isinstance(raw, str): continue
        s = raw.replace("/", ",").replace("·", ",").replace("•", ",").replace("|", ",")
        for t in s.split(","):
            t = _normalize(t)
            t = re.sub(r"\([^)]*\)", "", t)   # 괄호 제거
            t = re.sub(r"\b\d+(?:\.\d+)?\s*(개|g|kg|mg|ml|l|cup|cups|tsp|tbsp|큰술|작은술|스푼|숟가락|쪽|마리|줌|장|ea)\b", "", t)
            t = re.sub(r"\b\d+(?:/\d+)?\b", "", t)  # 숫자 잔여 제거
            t = t.strip()
            if not t: continue
            if t in STOPWORDS: continue
            if len(t) > 40: continue
            out.append(t)
    # 중복 제거
    seen, dedup = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); dedup.append(x)
    return dedup

def _match_and_missing(inv: List[str], rec_ing: List[str]) -> Tuple[List[str], List[str]]:
    inv_names = {_normalize(x) for x in inv}
    rec_tokens = set(_tokenize_ings(rec_ing))
    matched, missing = [], []
    for need in rec_tokens:
        hit = any(need in _expand_synonyms(iv) or iv in _expand_synonyms(need) for iv in inv_names)
        if hit: matched.append(need)
        else:   missing.append(need)
    return matched, missing

def _score_recipe(rec: RecipeItem, inventory: List[str], constraints: Dict[str, Any]) -> Optional[_Candidate]:
    allergies = constraints.get("allergies") or []
    dislikes = set(_normalize(x) for x in (constraints.get("dislikes") or []))
    max_missing = int(constraints.get("max_missing") or 3)

    # 알레르기/기피 필터
    if _contains_allergen(rec.ingredients, allergies):
        return None
    rec_tokens = set(_tokenize_ings(rec.ingredients))
    if any(_normalize(d) in rec_tokens for d in dislikes):
        return None

    # 매칭/누락
    uses, missing = _match_and_missing(inventory, rec.ingredients)
    if len(uses) == 0 or len(missing) > max_missing:
        return None

    # 저염식 등 헬스 컨텍스트 반영 소폭 가산
    health_bonus = 0
    diet = (constraints.get("diet") or "").lower()
    if diet == "low_sodium" and rec.nutrition and rec.nutrition.sodium_mg is not None:
        if rec.nutrition.sodium_mg <= 700:  # 서비스 규칙 가이드
            health_bonus += 8

    # 점수: 누락 0 우선 + 커버리지 + 헬스 보너스
    coverage = len(uses) / max(1, len(uses) + len(missing))
    score = (100 if len(missing) == 0 else 60 - 5*len(missing)) + 40*coverage + health_bonus

    return _Candidate(
        rec=rec,
        score=score,
        missing_count=len(missing),
        matched_count=len(uses),
        uses=uses,
        missing=missing
    )

# ------------------- OpenAI 유틸 -------------------
def _openai_client(constraints: Dict[str, Any]):
    try:
        from openai import OpenAI
        api_key = constraints.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set; OpenAI stages will be skipped.")
            return None
        os.environ["OPENAI_API_KEY"] = api_key
        return OpenAI()
    except Exception as e:
        logger.error(f"OpenAI import/init failed: {e}")
        return None

def _parse_json_safe(txt: str) -> Any:
    txt = (txt or "").strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.MULTILINE)
    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}|\[.*\]", txt, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

def _ensure_test_profile(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """
    프로필이 빈 경우 테스트 데이터를 주입해 why/suitability가 풍부해지도록 함.
    """
    c = dict(constraints or {})
    if not c.get("allergies") and not c.get("dislikes") and not c.get("diet") and not c.get("preferred_cuisines"):
        c.update({
            "allergies": ["새우"],          # 예시
            "dislikes": ["고수"],
            "diet": "low_sodium",          # 저염식 목표
            "preferred_cuisines": ["korean", "japanese"],
            "health_context": {
                "hypertension": True,
                "protein_target_g_per_meal": 25
            }
        })
    return c

# ------------------- LLM 스키마/프롬프트 -------------------
def _schema_spec(include_source: bool) -> Dict[str, Any]:
    source_prop = {"type":"object","properties":{"name":{"type":"string"},"url":{"type":"string"}}} if include_source else {"type":"object"}
    return {
        "type":"object",
        "required":["recipes"],
        "properties":{
            "recipes":{
                "type":"array",
                "items":{
                    "type":"object",
                    "required":["title","ingredients","steps"],
                    "properties":{
                        "title":{"type":"string","description":"한국어 제목"},
                        "ingredients":{"type":"array","items":{"type":"string"}},
                        "steps":{"type":"array","items":{"type":"string"}, "description":"모든 단계 한국어"},
                        "time_minutes":{"type":"integer"},
                        "time_breakdown":{"type":"object","properties":{"prep":{"type":"integer"},"cook":{"type":"integer"},"total":{"type":"integer"}}},
                        "servings":{"type":"integer"},
                        "difficulty":{"type":"string"},
                        "tags":{"type":"array","items":{"type":"string"}},
                        "source": source_prop,
                        "nutrition":{"type":"object","properties":{"calories_kcal":{"type":"integer"},"protein_g":{"type":"number"},"carbs_g":{"type":"number"},"fat_g":{"type":"number"},"sodium_mg":{"type":"integer"}}},
                        "allergens":{"type":"array","items":{"type":"string"}},
                        "equipment":{"type":"array","items":{"type":"string"}},
                        "substitutions":{"type":"object"},
                        "storage":{"type":"string"},
                        "reheat":{"type":"string"},
                        "suitability":{
                            "type":"object",
                            "properties":{
                                "summary":{"type":"string"},
                                "health":{"type":"string"},
                                "inventory":{"type":"string"},
                                "time":{"type":"string"},
                                "occasion":{"type":"string"},
                                "skill":{"type":"string"},
                                "tips":{"type":"array","items":{"type":"string"}},
                                "warnings":{"type":"array","items":{"type":"string"}}
                            }
                        }
                    }
                }
            }
        }
    }

def _web_find_prompt(inv: List[str], constraints: Dict[str, Any], need: int) -> Dict[str, Any]:
    c = _ensure_test_profile(constraints)
    req = {
        "inventory": inv,
        "allergies": c.get("allergies") or [],
        "dislikes": c.get("dislikes") or [],
        "diet": c.get("diet"),
        "preferred_cuisines": c.get("preferred_cuisines") or [],
        "health_context": c.get("health_context"),
        "time_min": c.get("time_min"),
        "time_max": c.get("time_max"),
        "max_missing": int(c.get("max_missing") or 3),
        "target_count": need,
        "note": "신뢰 가능한 출처 URL이 분명하면 포함, 불명확하면 생략 가능"
    }
    system = (
        "당신은 조리 연구 보조원입니다. 실제 브라우징 없이 지식과 검색능력을 활용해 "
        "신뢰 가능한 웹 레시피를 한국어로 요약하세요. 오직 JSON만 반환하세요."
    )
    user = {
        "output_contract": _schema_spec(include_source=True),
        "instruction": (
            "다음 조건을 만족하는 레시피를 최대 {k}개 반환하세요. "
            "인벤토리를 최대 활용하고 누락 재료는 max_missing 이하로 유지합니다. "
            "알레르기/기피를 피하고, diet/health_context/시간 제약을 반영하세요. "
            "제목/단계/설명은 한국어, JSON 외 텍스트 금지."
        ).format(k=need),
        "context": req
    }
    return {"system": system, "user": user}

def _synthesize_prompt(inv: List[str], constraints: Dict[str, Any], need: int) -> Dict[str, Any]:
    c = _ensure_test_profile(constraints)
    req = {
        "inventory": inv,
        "allergies": c.get("allergies") or [],
        "dislikes": c.get("dislikes") or [],
        "diet": c.get("diet"),
        "preferred_cuisines": c.get("preferred_cuisines") or [],
        "health_context": c.get("health_context"),
        "time_min": c.get("time_min"),
        "time_max": c.get("time_max"),
        "max_missing": int(c.get("max_missing") or 3),
        "target_count": need
    }
    system = (
        "당신은 프로 레시피 개발자입니다. 인벤토리를 최대 활용하고, "
        "알레르기/기피를 피하며, 식단/건강 목표와 시간 제약을 준수하세요. "
        "모든 텍스트는 한국어, 오직 JSON만 반환하세요."
    )
    user = {
        "output_contract": _schema_spec(include_source=False),
        "instruction": (
            "한국 가정식 중심으로 {k}개 생성하세요. "
            "누락 재료는 max_missing 이하로, 가능하면 대체재를 함께 제안하세요. "
            "JSON 외 텍스트 금지."
        ).format(k=need),
        "context": req
    }
    return {"system": system, "user": user}

# ------------------- OpenAI 호출 -------------------
def _openai_call(system: str, user_payload: Dict[str, Any], constraints: Dict[str, Any], temperature: float):
    client = _openai_client(constraints)
    if client is None:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":json.dumps(user_payload, ensure_ascii=False)}
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return None

def _openai_find_web_recipes(inventory: List[str], constraints: Dict[str, Any], need: int) -> List[RecipeItem]:
    p = _web_find_prompt(inventory, constraints, need)
    raw = _openai_call(p["system"], p["user"], constraints, temperature=0.4)
    data = _parse_json_safe(raw) if raw else None
    items = (data or {}).get("recipes") or []
    out: List[RecipeItem] = []
    for r in items:
        try:
            out.append(RecipeItem(**r))
        except Exception:
            continue
    return out

def _openai_generate_synthetic(inventory: List[str], constraints: Dict[str, Any], need: int) -> List[RecipeItem]:
    p = _synthesize_prompt(inventory, constraints, need)
    raw = _openai_call(p["system"], p["user"], constraints, temperature=0.6)
    data = _parse_json_safe(raw) if raw else None
    items = (data or {}).get("recipes") or []
    out: List[RecipeItem] = []
    for r in items:
        try:
            r.setdefault("source", {"name":"synthetic"})
            out.append(RecipeItem(**r))
        except Exception:
            continue
    return out

# ------------------- 마케팅 카피 생성 -------------------
def _marketing_headline(rec: RecipeItem, uses: List[str], constraints: Dict[str, Any]) -> str:
    c = _ensure_test_profile(constraints)
    diet = (c.get("diet") or "").lower()
    time_max = c.get("time_max")
    pref = c.get("preferred_cuisines") or []
    focus = []
    if uses:
        focus.append(f"냉장고 속 {', '.join(uses[:3])}로")
    if time_max:
        focus.append(f"{time_max}분 컷")
    if diet == "low_sodium":
        focus.append("저염 한끼")
    if "korean" in [p.lower() for p in pref]:
        focus.append("집밥 감성")
    if not focus:
        focus.append("간단하고 든든하게")

    # 카피라이팅 톤
    return f"{' · '.join(focus)} — 지금 바로 즐기는 「{rec.title}」"

# ------------------- 고객 UI용 카드 텍스트 -------------------
def _build_customer_card(rec: RecipeItem, uses: List[str], missing: List[str], constraints: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"• 한 줄 요약: {_marketing_headline(rec, uses, constraints)}")
    if rec.nutrition:
        macro = []
        if rec.nutrition.calories_kcal is not None: macro.append(f"{rec.nutrition.calories_kcal} kcal")
        if rec.nutrition.protein_g is not None: macro.append(f"단백질 {rec.nutrition.protein_g}g")
        if rec.nutrition.carbs_g is not None: macro.append(f"탄수화물 {rec.nutrition.carbs_g}g")
        if rec.nutrition.fat_g is not None: macro.append(f"지방 {rec.nutrition.fat_g}g")
        if rec.nutrition.sodium_mg is not None: macro.append(f"나트륨 {rec.nutrition.sodium_mg}mg")
        if macro: lines.append("• 영양 요약(1인분): " + ", ".join(macro))
    if rec.suitability:
        if rec.suitability.health: lines.append(f"• 건강 포인트: {rec.suitability.health}")
        if rec.suitability.inventory: lines.append(f"• 인벤토리 활용: {rec.suitability.inventory}")
        if rec.suitability.time: lines.append(f"• 시간 적합성: {rec.suitability.time}")
        if rec.suitability.occasion: lines.append(f"• 어울리는 순간: {rec.suitability.occasion}")
        if rec.suitability.skill: lines.append(f"• 난이도/스킬: {rec.suitability.skill}")
        if rec.suitability.tips: lines.append("• 팁: " + "; ".join(rec.suitability.tips[:3]))
        if rec.suitability.warnings: lines.append("• 주의: " + "; ".join(rec.suitability.warnings[:2]))
    if uses:
        lines.append("• 냉장고에서 사용하는 재료: " + ", ".join(uses))
    if missing:
        lines.append("• 쇼핑리스트(누락): " + ", ".join(missing))
    if rec.storage: lines.append(f"• 보관: {rec.storage}")
    if rec.reheat: lines.append(f"• 재가열: {rec.reheat}")
    # cost_tier / co2_footprint_note는 제거(요청사항)
    return "\n".join(lines)

# ------------------- 공개 인터페이스 -------------------
def suggest_recipes(ingredients: List[str], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Input:
      ingredients: ["계란","양파","대파", ...]
      constraints:
        - allergies, dislikes, diet, preferred_cuisines, time_min/time_max
        - openai_api_key
        - target_count (기본 3), max_missing (기본 3)

    Output (프론트 직결):
      [{
        "id","title","ingredients","steps","time_minutes","time_breakdown","servings",
        "source","nutrition","allergens","equipment","substitutions",
        "storage","reheat",
        "difficulty","tags","uses","missing","suitability","customer_card"
      }, ...]
    """
    target = int(constraints.get("target_count") or 3)
    inv_norm = [_normalize(x) for x in ingredients if _normalize(x)]
    partial: List[Dict[str, Any]] = []

    # 1) 웹 요약
    web_recipes = _openai_find_web_recipes(inv_norm, constraints, need=target*2)
    cands: List[_Candidate] = []
    for r in web_recipes:
        cand = _score_recipe(r, inv_norm, constraints)
        if cand: cands.append(cand)

    # 2) 부족하면 창작
    if len(cands) < target:
        synth = _openai_generate_synthetic(inv_norm, constraints, need=(target - len(cands))*2)
        for r in synth:
            cand = _score_recipe(r, inv_norm, constraints)
            if cand: cands.append(cand)

    # 정렬 및 빌드
    cands.sort(key=lambda c: (c.missing_count, -c.matched_count, -c.score))
    results: List[Dict[str, Any]] = []
    seen_titles = set()
    for c in cands:
        if c.rec.title in seen_titles:
            continue
        seen_titles.add(c.rec.title)
        rec = c.rec.model_dump()
        rec["uses"] = c.uses
        rec["missing"] = c.missing
        rec["id"] = _stable_id(rec.get("title",""), "|".join(c.uses))
        rec["customer_card"] = _build_customer_card(c.rec, c.uses, c.missing, constraints)
        results.append(rec)
        if len(results) >= target:
            break

    return results

# ------------------- CLI -------------------
if __name__ == "__main__":
    import argparse, sys, json as _json
    p = argparse.ArgumentParser()
    p.add_argument("--inv", type=str, default="data/sample_inventory.json")
    p.add_argument("--target_count", type=int, default=3)
    p.add_argument("--diet", type=str, default=None)
    p.add_argument("--time_max", type=int, default=None)
    p.add_argument("--max_missing", type=int, default=3)
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # 인벤토리/프로필 로드
    try:
        with open(args.inv, "r", encoding="utf-8") as f:
            j = _json.load(f)
        inv = [x["name"] for x in j.get("inventory", [])]
        profile = j.get("user_profile", {})
        allergies = profile.get("allergies", [])
        dislikes  = profile.get("dislikes", [])
        preferred = profile.get("preferred_cuisines", [])
        diet_goal = profile.get("diet_goal")
        health_ctx = profile.get("health_context")
    except Exception as e:
        logger.error(f"failed to read inventory json: {e}")
        sys.exit(1)

    constraints = {
        "allergies": allergies,
        "dislikes": dislikes,
        "diet": args.diet or diet_goal,
        "preferred_cuisines": preferred,
        "time_max": args.time_max,
        "target_count": args.target_count,
        "max_missing": args.max_missing,
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    }
    if health_ctx:
        constraints["health_context"] = health_ctx
    constraints = _ensure_test_profile(constraints)

    out = suggest_recipes(inv, constraints)
    if not out:
        print("[INFO] 결과가 0개입니다. 점검: OPENAI_API_KEY, 네트워크, 제약조건 과도 여부")
    else:
        for i, r in enumerate(out, 1):
            src = r.get("source", {}) or {}
            src_disp = f"  [{src.get('name')}]" if src.get("name") else ""
            url_disp = f"  <{src.get('url')}>" if src.get("url") else ""
            print(f"{i}. {r['title']}{src_disp}{url_disp}")
            print(f"   id: {r.get('id')}")
            print(f"   time: {r.get('time_minutes')}  breakdown: {r.get('time_breakdown')}")
            print(f"   servings: {r.get('servings')}  difficulty: {r.get('difficulty')}  tags: {r.get('tags')}")
            print(f"   uses: {r.get('uses', [])}")
            print(f"   missing: {r.get('missing', [])}")
            if r.get("nutrition"):
                print(f"   nutrition: {r['nutrition']}")
            print("   customer_card:")
            print("   " + r.get("customer_card","").replace("\n","\n   "))