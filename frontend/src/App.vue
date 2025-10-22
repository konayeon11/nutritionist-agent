<template>
  <div class="app">
    <!-- 상단 바 (레시피 상세 뷰가 아닐 때만 표시) -->
    <div class="topbar" v-if="currentView !== 'recipeDetail'">
      <div class="app-title">
        <img src="/miri-logo.png" alt="MIRI Logo" class="logo" />
        <div class="title-col">
          <b>미리 (MIRI)</b>
          <span class="small">당신의 식탁을 미리 준비합니다</span>
        </div>
      </div>
      <div class="hud">
        <div class="pill">Lv.{{ level }}</div>
        <div class="xpbar"><i :style="{width: xpPct + '%'}"></i></div>
      </div>
    </div>

    <div class="content">
      <!-- 메인 뷰: 이미지 업로드 및 레시피 추천 -->
      <template v-if="currentView === 'main'">
        <section class="panel">
          <div class="ph">냉장고 사진 스캔하기</div>
          <div class="section upload">
            <div class="filebox">
              <input type="file" accept="image/*" @change="handleFileUpload" ref="fileInput" />
            </div>
            <div v-if="previewURL" class="preview">
              <img :src="previewURL" alt="preview"/>
              <div class="small">스캔할 사진 미리보기</div>
            </div>

            <input type="text" v-model="promptText" placeholder="예) 20분 내 단백질 위주 레시피" />

            <div class="btn-row">
              <button @click="analyzeImage" :disabled="isLoading || !selectedFile">
                {{ isLoading ? "⏳ 분석 중..." : "🍳 레시피 추천받기" }}
              </button>
            </div>
          </div>
        </section>

        <!-- 추천 레시피 표시 -->
        <section v-if="latestRecipes.length > 0" class="panel">
          <div class="ph">✨ 오늘의 추천 레시피 ({{ latestRecipes.length }}개)</div>
          <div class="section" style="display:flex;flex-direction:column;gap:10px">
            <div v-for="(recipe, idx) in latestRecipes" :key="idx"
                 class="recipe-card" @click="viewRecipeDetail(recipe)">
              <div class="rc-title">
                <b>{{ recipe.title }}</b>
              </div>
              <ul class="rc-meta" v-if="recipe.time_minutes || recipe.nutrition">
                <li v-if="recipe.time_minutes"><strong>예상 시간:</strong> {{ recipe.time_minutes }}분</li>
                <li v-if="recipe.nutrition">
                  <span class="nutrition-badge">
                    🔥 {{ recipe.nutrition.calories_kcal || 'N/A' }}kcal
                  </span>
                  <span class="nutrition-badge">
                    💪 {{ recipe.nutrition.protein_g || 'N/A' }}g 단백질
                  </span>
                </li>
                <li v-if="recipe.missing && recipe.missing.length > 0">
                  <i>추가 필요: {{ recipe.missing.join(', ') }}</i>
                </li>
                <li v-else>
                  <i style="color: var(--good)">추가 재료 없음!</i>
                </li>
              </ul>
              <div style="margin-top:12px">
                <button @click.stop="viewRecipeDetail(recipe)" class="detail-btn">
                  📖 레시피 상세 보기
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- 쇼핑 리스트 -->
        <section v-if="shoppingList && shoppingList.items && shoppingList.items.length > 0" class="panel">
          <div class="ph">🛒 부족한 재료 구매하기</div>
          <div class="section">
            <div class="shopping-grid">
              <a v-for="(item, idx) in shoppingList.items" :key="idx"
                 :href="item.url"
                 target="_blank"
                 class="shopping-item">
                <div class="shopping-icon">🛍️</div>
                <div class="shopping-info">
                  <div class="shopping-name">{{ item.name }}</div>
                  <div class="shopping-qty">{{ item.quantity }}</div>
                </div>
                <div class="shopping-arrow">→</div>
              </a>
            </div>
          </div>
        </section>

        <!-- 일일 퀘스트 -->
        <section v-if="quests.length > 0" class="panel">
          <div class="ph">🎯 일일 퀘스트 ({{ quests.length }}개)</div>
          <div class="section" style="display:flex;flex-direction:column;gap:10px">
            <div v-for="quest in quests" :key="quest.id" class="quest-card">
              <div class="quest-header">
                <div class="quest-title">
                  <b>{{ quest.title }}</b>
                  <span class="xp-badge">+{{ quest.xp }}XP</span>
                </div>
              </div>
              <div class="quest-reason">{{ quest.reason }}</div>
              <div class="quest-checks" v-if="quest.checks && quest.checks.length > 0">
                <div v-for="(check, idx) in quest.checks" :key="idx" class="check-item">
                  ☐ {{ check }}
                </div>
              </div>
              <button
                @click="completeQuest(quest)"
                :disabled="completedQuests.has(quest.id)"
                class="quest-btn"
                :class="{'completed': completedQuests.has(quest.id)}">
                {{ completedQuests.has(quest.id) ? '✅ 완료됨' : '완료하기' }}
              </button>
            </div>
          </div>
        </section>

        <!-- 실행 로그 -->
        <section v-if="logs.length > 0" class="panel">
          <div class="ph">실행 로그</div>
          <div class="section">
            <div class="log">
              <div v-for="(msg, i) in logs" :key="i" class="msg">
                <div class="avatar-b"></div>
                <div class="bubble" v-html="msg"></div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- 인벤토리 뷰 -->
      <template v-else-if="currentView === 'inventory'">
        <section class="panel">
          <div class="ph">냉장고 인벤토리 관리</div>
          <div class="section">
            <p v-if="!inventory || Object.keys(inventory).length === 0" class="small" style="text-align: center; padding: 50px 0;">
              메인 페이지에서 냉장고 사진을 스캔해야<br>재료 목록이 표시됩니다.
            </p>
            <div v-else class="inv-grid">
              <div v-for="[name, item] in sortedInventory" :key="name"
                   class="inv-card"
                   :class="{'expiring': daysLeft(item.expiry_date) <= 3 && daysLeft(item.expiry_date) >= 0,
                            'expired': daysLeft(item.expiry_date) < 0}">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <b>{{ name }}</b>
                  <span class="badge">{{ item.quantity }}</span>
                </div>
                <div class="small">D{{ dday(item.expiry_date) }} · {{ item.expiry_date }}</div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- 챗봇 뷰 (기존 채팅 기능 유지) -->
      <template v-else-if="currentView === 'chatbot'">
        <div class="chat-container">
          <div class="message-area" ref="messageArea">
            <div v-for="(message, index) in messages" :key="index" class="message-wrapper" :class="message.sender">
              <div class="message-bubble">
                <img v-if="message.image" :src="message.image" alt="Uploaded content" class="uploaded-image" />
                <p v-else v-html="formatMessage(message.text)"></p>
              </div>
            </div>
            <div v-if="isChatLoading" class="message-wrapper assistant">
              <div class="message-bubble loading-bubble"><div class="dot-flashing"></div></div>
            </div>
          </div>
          <form @submit.prevent="sendChatMessage" class="input-area">
            <label for="chat-file-upload" class="file-upload-label">📎</label>
            <input id="chat-file-upload" type="file" @change="handleChatFileUpload" accept="image/*" />
            <input type="text" v-model="chatMessage" :placeholder="chatFile ? chatFile.name : '재료를 입력하거나 사진을 첨부하세요...'" :disabled="isChatLoading" />
            <button type="submit" :disabled="isChatLoading || (!chatFile && !chatMessage.trim())">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M3 20V4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v16l-4-4H5a2 2 0 0 1-2-2Z"/></svg>
            </button>
          </form>
        </div>

        <!-- 챗봇에서 추천받은 레시피 목록 -->
        <section v-if="chatLatestRecipes.length > 0" class="panel" style="margin-top: 16px;">
          <div class="ph">✨ 추천 레시피 ({{ chatLatestRecipes.length }}개)</div>
          <div class="section" style="display:flex;flex-direction:column;gap:10px">
            <div v-for="(recipe, idx) in chatLatestRecipes" :key="idx"
                 class="recipe-card" @click="viewRecipeDetail(recipe)">
              <div class="rc-title">
                <b>{{ recipe.title }}</b>
              </div>
              <ul class="rc-meta" v-if="recipe.time_minutes || recipe.nutrition">
                <li v-if="recipe.time_minutes"><strong>예상 시간:</strong> {{ recipe.time_minutes }}분</li>
                <li v-if="recipe.nutrition">
                  <span class="nutrition-badge">
                    🔥 {{ recipe.nutrition.calories_kcal || 'N/A' }}kcal
                  </span>
                  <span class="nutrition-badge">
                    💪 {{ recipe.nutrition.protein_g || 'N/A' }}g 단백질
                  </span>
                </li>
                <li v-if="recipe.missing && recipe.missing.length > 0">
                  <i>추가 필요: {{ recipe.missing.join(', ') }}</i>
                </li>
                <li v-else>
                  <i style="color: var(--good)">추가 재료 없음!</i>
                </li>
              </ul>
              <div style="margin-top:12px">
                <button @click.stop="viewRecipeDetail(recipe)" class="detail-btn">
                  📖 레시피 상세 보기
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- 챗봇 내 레시피 상세 보기 (인라인) -->
        <section v-if="selectedRecipe" class="panel recipe-detail-inline" style="margin-top: 16px;">
          <div class="ph" style="display:flex;justify-content:space-between;align-items:center;">
            <span>📖 {{ selectedRecipe.title }}</span>
            <button @click="selectedRecipe = null" class="close-btn">✕ 닫기</button>
          </div>
          <div class="section">
            <div v-if="selectedRecipe.image" style="margin-bottom:16px;">
              <img :src="selectedRecipe.image" :alt="selectedRecipe.title" style="width:100%;border-radius:8px;"/>
            </div>

            <div class="detail-meta">
              <span v-if="selectedRecipe.time_minutes">⏱️ {{ selectedRecipe.time_minutes }}분</span>
              <span v-if="selectedRecipe.servings">🍽️ {{ selectedRecipe.servings }}인분</span>
              <span v-if="selectedRecipe.difficulty">📊 {{ selectedRecipe.difficulty }}</span>
            </div>

            <div v-if="selectedRecipe.nutrition" class="nutrition-info">
              <h4>영양 정보 (1인분 기준)</h4>
              <div class="nutrition-grid">
                <span>🔥 {{ selectedRecipe.nutrition.calories_kcal }}kcal</span>
                <span>💪 단백질 {{ selectedRecipe.nutrition.protein_g }}g</span>
                <span>🍚 탄수화물 {{ selectedRecipe.nutrition.carbs_g }}g</span>
                <span>🧈 지방 {{ selectedRecipe.nutrition.fat_g }}g</span>
              </div>
            </div>

            <div v-if="selectedRecipe.ingredients" class="ingredients">
              <h4>🥘 필요한 재료</h4>
              <ul>
                <li v-for="(ing, i) in selectedRecipe.ingredients" :key="i">{{ ing }}</li>
              </ul>
            </div>

            <div v-if="selectedRecipe.steps" class="steps">
              <h4>👨‍🍳 조리 순서</h4>
              <ol>
                <li v-for="(step, i) in selectedRecipe.steps" :key="i">{{ step }}</li>
              </ol>
            </div>
          </div>
        </section>
      </template>

      <!-- 프로필 뷰 -->
      <template v-else-if="currentView === 'profile'">
        <section class="panel">
          <div class="ph">👤 내 프로필 및 목표 설정</div>
          <div class="section">
            <p style="margin-bottom: 20px; color: var(--text-medium); font-size: 14px; line-height: 1.6;">
              영양 및 레시피 추천의 정확도를 높이기 위해 필요한 정보입니다.<br>
              입력한 정보는 브라우저에 안전하게 저장됩니다.
            </p>
            <div class="profile-form">
              <div class="form-group">
                <label for="goal">🎯 건강 목표</label>
                <input
                  id="goal"
                  type="text"
                  v-model="userProfile.goal"
                  placeholder="예: 체중 감량, 근육 증가, 건강 유지"
                />
                <span class="form-hint">달성하고 싶은 건강 목표를 입력하세요</span>
              </div>

              <div class="form-group">
                <label for="diet">🍽️ 원하는 식단</label>
                <input
                  id="diet"
                  type="text"
                  v-model="userProfile.diet"
                  placeholder="예: 일반식, 채식, 저탄수화물, 고단백"
                />
                <span class="form-hint">선호하는 식단 유형을 입력하세요</span>
              </div>

              <div class="form-group">
                <label for="age">🎂 나이</label>
                <input
                  id="age"
                  type="number"
                  v-model.number="userProfile.age"
                  placeholder="예: 30"
                  min="1"
                  max="120"
                />
                <span class="form-hint">레시피 추천에 참고됩니다</span>
              </div>

              <div class="form-group">
                <label for="allergies">🚫 알레르기</label>
                <input
                  id="allergies"
                  type="text"
                  v-model="userProfile.allergies"
                  placeholder="예: 새우, 땅콩, 우유"
                />
                <span class="form-hint">알레르기가 있는 식재료를 쉼표(,)로 구분하여 입력하세요</span>
              </div>

              <button class="save-profile-btn" @click="saveProfile">
                💾 정보 저장
              </button>

              <div v-if="profileSaved" class="save-success">
                ✅ 프로필이 성공적으로 저장되었습니다!
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- 레시피 상세 뷰 -->
      <template v-else-if="currentView === 'recipeDetail' && selectedRecipe">
        <div class="recipe-detail-view">
          <button @click="closeRecipeDetail" class="back-button">
            ← 목록으로 돌아가기
          </button>

          <h2>{{ selectedRecipe.title }}</h2>

          <div class="detail-meta">
            <span v-if="selectedRecipe.difficulty">난이도: {{ selectedRecipe.difficulty }}</span>
            <span v-if="selectedRecipe.time_minutes">{{ selectedRecipe.time_minutes }}분</span>
            <span v-if="selectedRecipe.servings">{{ selectedRecipe.servings }}인분</span>
          </div>

          <div class="detail-section" v-if="selectedRecipe.ingredients && selectedRecipe.ingredients.length > 0">
            <h3>필요 재료</h3>
            <ul>
              <li v-for="(ing, i) in selectedRecipe.ingredients" :key="'ing'+i">{{ ing }}</li>
            </ul>
          </div>

          <div class="detail-section" v-if="selectedRecipe.steps && selectedRecipe.steps.length > 0">
            <h3>조리 순서</h3>
            <ol>
              <li v-for="(step, i) in selectedRecipe.steps" :key="'step'+i">{{ step }}</li>
            </ol>
          </div>

          <div class="detail-section" v-if="selectedRecipe.nutrition">
            <h3>영양 정보 (1인분)</h3>
            <p>
              <strong>칼로리:</strong> {{ selectedRecipe.nutrition.calories_kcal || 'N/A' }}kcal |
              <strong>단백질:</strong> {{ selectedRecipe.nutrition.protein_g || 'N/A' }}g |
              <strong>탄수화물:</strong> {{ selectedRecipe.nutrition.carbs_g || 'N/A' }}g |
              <strong>지방:</strong> {{ selectedRecipe.nutrition.fat_g || 'N/A' }}g |
              <strong>나트륨:</strong> {{ selectedRecipe.nutrition.sodium_mg || 'N/A' }}mg
            </p>
          </div>

          <div class="detail-section" v-if="selectedRecipe.source && selectedRecipe.source.url">
            <a :href="selectedRecipe.source.url" target="_blank" class="source-link">
              레시피 출처 보기
            </a>
          </div>
        </div>
      </template>
    </div>

    <!-- 하단 네비게이션 바 -->
    <div class="bottom-nav" v-if="currentView !== 'recipeDetail'">
      <div class="nav-item" :class="{active: currentView === 'main'}" @click="navigate('main')">
        <div class="nav-icon">🏠</div>
        <span>레시피 추천</span>
      </div>
      <div class="nav-item" :class="{active: currentView === 'inventory'}" @click="navigate('inventory')">
        <div class="nav-icon">🍎</div>
        <span>냉장고 재료</span>
      </div>
      <div class="nav-item" :class="{active: currentView === 'chatbot'}" @click="navigate('chatbot')">
        <div class="nav-icon">💬</div>
        <span>AI 챗봇</span>
      </div>
      <div class="nav-item" :class="{active: currentView === 'profile'}" @click="navigate('profile')">
        <div class="nav-icon">👤</div>
        <span>마이 프로필</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue';

// 상태 관리
const currentView = ref('main'); // 'main', 'inventory', 'chatbot', 'profile', 'recipeDetail'
const previousView = ref('main'); // 레시피 상세보기 이전 페이지 기억
const selectedFile = ref(null);
const previewURL = ref('');
const promptText = ref('');
const isLoading = ref(false);
const logs = ref([]);
const latestRecipes = ref([]);
const inventory = ref({});
const selectedRecipe = ref(null);
const shoppingList = ref(null);

// 레벨/XP 시스템
const level = ref(1);
const xp = ref(0);
const xpNext = ref(100);
const xpPct = computed(() => Math.round(100 * xp.value / xpNext.value));
const quests = ref([]);
const completedQuests = ref(new Set());

// 유통기한 임박 순서로 정렬된 인벤토리
const sortedInventory = computed(() => {
  const items = Object.entries(inventory.value);
  return items.sort((a, b) => {
    const dateA = new Date(a[1].expiry_date + 'T00:00:00');
    const dateB = new Date(b[1].expiry_date + 'T00:00:00');
    return dateA - dateB; // 오름차순 정렬 (빠른 날짜가 먼저)
  });
});

// 챗봇 관련
const messages = ref([
  { sender: 'assistant', text: '안녕하세요! 저는 미리(MIRI)입니다. 🍳<br>당신의 식탁을 미리 준비하는 AI 영양사예요.<br>재료를 입력하시거나 📎 버튼으로 냉장고 사진을 보내주세요!' }
]);
const chatMessage = ref('');
const chatFile = ref(null);
const isChatLoading = ref(false);
const messageArea = ref(null);
const chatLatestRecipes = ref([]);

// 프로필
const userProfile = reactive({
  goal: '체중 관리',
  diet: '일반식',
  age: 30,
  allergies: ''
});
const profileSaved = ref(false);

// 헬스 체크
const healthStatus = ref('확인 중...');

const fileInput = ref(null);

// 네비게이션
const navigate = async (view) => {
  currentView.value = view;
  selectedRecipe.value = null;
  window.scrollTo(0, 0);

  // 인벤토리 뷰로 이동할 때 데이터 로드
  if (view === 'inventory') {
    await loadInventory();
  }
};

// 인벤토리 로드
const loadInventory = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/inventory');
    if (!response.ok) throw new Error('인벤토리 로드 실패');
    const result = await response.json();

    // items를 inventory 형식으로 변환
    if (result.items) {
      inventory.value = result.items;
    }
  } catch (error) {
    console.error('인벤토리 로드 오류:', error);
    addLog('❌ 인벤토리를 불러오는데 실패했습니다.');
  }
};

// 파일 업로드 (메인)
const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    previewURL.value = URL.createObjectURL(file);
  }
};

// 이미지 분석
const analyzeImage = async () => {
  if (!selectedFile.value || isLoading.value) return;

  isLoading.value = true;
  logs.value = [];
  latestRecipes.value = [];

  addLog('📤 이미지를 업로드하고 분석을 시작합니다...');

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);

    // 알레르기 문자열을 배열로 변환
    const allergiesList = userProfile.allergies
      ? userProfile.allergies.split(',').map(item => item.trim()).filter(item => item)
      : [];

    formData.append('constraints', JSON.stringify({
      prompt: promptText.value || '레시피 추천',
      dietary_goals: userProfile.diet || userProfile.goal,  // 식단 선호도 또는 목표
      user_goal: userProfile.goal,  // 건강 목표
      user_age: userProfile.age,     // 나이
      allergies: allergiesList        // 알레르기 목록
    }));

    const response = await fetch('http://127.0.0.1:8000/analyze-and-suggest', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    const result = await response.json();

    // 결과 처리
    if (result.inventory) {
      inventory.value = result.inventory;
      const ingredientNames = Object.keys(result.inventory);
      addLog(`✅ 인식된 재료: ${ingredientNames.join(', ')}`);
    }

    if (result.recipes && result.recipes.length > 0) {
      latestRecipes.value = result.recipes;
      addLog(`✅ ${result.recipes.length}개의 레시피를 추천합니다!`);
    }

    if (result.shopping_list) {
      shoppingList.value = result.shopping_list;
      addLog(`🛒 부족한 재료 ${result.shopping_list.items?.length || 0}개를 찾았습니다!`);
    }

    if (result.quests && result.quests.length > 0) {
      quests.value = result.quests;
      addLog(`🎯 ${result.quests.length}개의 일일 퀘스트가 생성되었습니다!`);
    }

    addLog('✅ 분석 완료!');
  } catch (error) {
    console.error('API 요청 실패:', error);
    addLog(`❌ 오류: ${error.message}`);
  } finally {
    isLoading.value = false;
  }
};

// 로그 추가
const addLog = (message) => {
  logs.value.push(message);
};

// XP 획득
const gainXP = (amount) => {
  xp.value += amount;
  while (xp.value >= xpNext.value) {
    level.value += 1;
    xp.value -= xpNext.value;
    xpNext.value = Math.round(xpNext.value * 1.25);
    addLog(`🎉 레벨 업! Lv.${level.value} 달성`);
  }
};

// 퀘스트 완료
const completeQuest = (quest) => {
  if (completedQuests.value.has(quest.id)) {
    addLog('이미 완료한 퀘스트입니다.');
    return;
  }

  completedQuests.value.add(quest.id);
  gainXP(quest.xp);
  addLog(`✅ '${quest.title}' 완료! +${quest.xp}XP`);
};

// 레시피 상세 보기
const viewRecipeDetail = (recipe) => {
  selectedRecipe.value = recipe;
  // 챗봇에서는 페이지 이동 없이 인라인 표시
  if (currentView.value === 'chatbot') {
    // 챗봇 내에서 스크롤만
    nextTick(() => {
      const detailEl = document.querySelector('.recipe-detail-inline');
      if (detailEl) detailEl.scrollIntoView({ behavior: 'smooth' });
    });
  } else {
    // 다른 뷰에서는 페이지 전환
    previousView.value = currentView.value;
    currentView.value = 'recipeDetail';
    window.scrollTo(0, 0);
  }
};

// 레시피 상세 닫기
const closeRecipeDetail = () => {
  selectedRecipe.value = null;
  currentView.value = previousView.value; // 이전 페이지로 돌아가기
};

// 인벤토리 유틸
const daysLeft = (dateStr) => {
  if (!dateStr) return 999;
  const d = new Date(dateStr + 'T00:00:00');
  const now = new Date();
  const diff = Math.ceil((d - now) / 86400000);
  return diff;
};

const dday = (dateStr) => {
  const left = daysLeft(dateStr);
  return (left >= 0 ? '+' : '') + left;
};

// 챗봇 파일 업로드
const handleChatFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    chatFile.value = file;
    chatMessage.value = '';
  }
};

// 챗봇 메시지 전송
const sendChatMessage = async () => {
  const hasFile = chatFile.value;
  const hasText = chatMessage.value.trim();
  if ((!hasFile && !hasText) || isChatLoading.value) return;

  isChatLoading.value = true;

  if (hasFile) {
    const file = chatFile.value;
    const imageUrl = URL.createObjectURL(file);
    messages.value.push({ sender: 'user', image: imageUrl });
    chatFile.value = null;
    scrollToBottom();
    await handleChatImageQuery(file);
  } else if (hasText) {
    const userMessage = chatMessage.value.trim();
    messages.value.push({ sender: 'user', text: userMessage });
    chatMessage.value = '';
    scrollToBottom();
    await handleChatTextQuery(userMessage);
  }
};

// 챗봇 이미지 쿼리
const handleChatImageQuery = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  // 알레르기 문자열을 배열로 변환
  const allergiesList = userProfile.allergies
    ? userProfile.allergies.split(',').map(item => item.trim()).filter(item => item)
    : [];

  formData.append('constraints', JSON.stringify({
    dietary_goals: userProfile.diet || userProfile.goal,
    user_goal: userProfile.goal,
    user_age: userProfile.age,
    allergies: allergiesList
  }));

  try {
    const response = await fetch('http://127.0.0.1:8000/analyze-and-suggest', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    const result = await response.json();
    displayChatAnalysisResult(result);
  } catch (error) {
    handleChatError(error);
  }
};

// 챗봇 텍스트 쿼리
const handleChatTextQuery = async (textMessage) => {
  try {
    // 알레르기 문자열을 배열로 변환
    const allergiesList = userProfile.allergies
      ? userProfile.allergies.split(',').map(item => item.trim()).filter(item => item)
      : [];

    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: textMessage,
        constraints: {
          dietary_goals: userProfile.diet || userProfile.goal,
          user_goal: userProfile.goal,
          user_age: userProfile.age,
          allergies: allergiesList
        }
      }),
    });
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    const result = await response.json();
    displayChatResult(result);
  } catch (error) {
    handleChatError(error);
  }
};

// 챗봇 분석 결과 표시
const displayChatAnalysisResult = (result) => {
  let assistantResponse = '분석이 완료되었습니다!<br><br>';
  if (result.inventory) {
    const ingredients = Object.keys(result.inventory);
    assistantResponse += `<b>[인식된 재료]</b><br>${ingredients.join(', ')}<br><br>`;
  }
  if (result.recipes && result.recipes.length > 0) {
    chatLatestRecipes.value = result.recipes;
    assistantResponse += '<b>[추천 레시피]</b><br>';
    result.recipes.forEach((recipe, i) => {
      assistantResponse += `<button class="chat-recipe-btn" data-recipe-index="${i}" onclick="return false;">📖 ${i + 1}. ${recipe.title}</button><br>`;
      if (recipe.missing && recipe.missing.length > 0) {
        assistantResponse += `<i style="margin-left: 10px;">추가 필요: ${recipe.missing.join(', ')}</i><br>`;
      } else {
        assistantResponse += `<i style="margin-left: 10px; color: var(--good);">추가 재료 없음!</i><br>`;
      }
      assistantResponse += '<br>';
    });
  }
  if (result.shopping_list && result.shopping_list.items && result.shopping_list.items.length > 0) {
    assistantResponse += '<br><b>[부족한 재료 구매하기 🛒]</b><br>';
    result.shopping_list.items.forEach(item => {
      assistantResponse += `<a href="${item.url}" target="_blank" class="chat-shopping-link">🛍️ ${item.name} (${item.quantity})</a><br>`;
    });
  }
  messages.value.push({ sender: 'assistant', text: assistantResponse });

  // 메시지 추가 후 이벤트 리스너 재등록
  nextTick(() => {
    attachChatRecipeListeners();
  });

  finalizeChatMessage();
};

// 챗봇 결과 표시
const displayChatResult = (result) => {
  let assistantResponse = result.response || '응답을 받을 수 없습니다.';

  if (result.recipes && result.recipes.length > 0) {
    chatLatestRecipes.value = result.recipes;
    assistantResponse += '<br><br><b>[추천 레시피]</b><br>';
    result.recipes.forEach((recipe, i) => {
      assistantResponse += `<button class="chat-recipe-btn" data-recipe-index="${i}" onclick="return false;">📖 ${i + 1}. ${recipe.title}</button><br>`;
      if (recipe.missing && recipe.missing.length > 0) {
        assistantResponse += `<i style="margin-left: 10px;">추가 필요: ${recipe.missing.join(', ')}</i><br>`;
      } else {
        assistantResponse += `<i style="margin-left: 10px; color: var(--good);">추가 재료 없음!</i><br>`;
      }
      assistantResponse += '<br>';
    });
  }
  if (result.shopping_list && result.shopping_list.items && result.shopping_list.items.length > 0) {
    assistantResponse += '<br><b>[부족한 재료 구매하기 🛒]</b><br>';
    result.shopping_list.items.forEach(item => {
      assistantResponse += `<a href="${item.url}" target="_blank" class="chat-shopping-link">🛍️ ${item.name} (${item.quantity})</a><br>`;
    });
  }
  messages.value.push({ sender: 'assistant', text: assistantResponse });

  // 메시지 추가 후 이벤트 리스너 재등록
  nextTick(() => {
    attachChatRecipeListeners();
  });

  finalizeChatMessage();
};

const handleChatError = (error) => {
  console.error('API 요청 실패:', error);
  messages.value.push({ sender: 'assistant', text: '죄송합니다, 서버와 통신 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.' });
  finalizeChatMessage();
};

const finalizeChatMessage = () => {
  isChatLoading.value = false;
  scrollToBottom();
};

const formatMessage = (text) => {
  return text.replace(/\n/g, '<br>');
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messageArea.value) {
      messageArea.value.scrollTop = messageArea.value.scrollHeight;
    }
  });
};

// 프로필 저장
const saveProfile = () => {
  localStorage.setItem('userProfile', JSON.stringify(userProfile));
  profileSaved.value = true;

  // 3초 후 성공 메시지 숨기기
  setTimeout(() => {
    profileSaved.value = false;
  }, 3000);
};

// 챗봇 레시피 버튼 이벤트 리스너 연결
const attachChatRecipeListeners = () => {
  if (!messageArea.value) return;

  const buttons = messageArea.value.querySelectorAll('.chat-recipe-btn');
  buttons.forEach((button) => {
    button.addEventListener('click', (event) => {
      event.preventDefault();
      const index = parseInt(button.dataset.recipeIndex);
      if (chatLatestRecipes.value[index]) {
        viewRecipeDetail(chatLatestRecipes.value[index]);
      }
    });
  });
};

// 헬스 체크
const checkHealth = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/health');
    if (response.ok) {
      healthStatus.value = '연결 정상';
    } else {
      healthStatus.value = '연결 확인 필요';
    }
  } catch (error) {
    healthStatus.value = '서버 연결 실패';
  }
};

onMounted(() => {
  checkHealth();
  loadInventory(); // 초기 인벤토리 로드
  // 저장된 프로필 불러오기
  const saved = localStorage.getItem('userProfile');
  if (saved) {
    Object.assign(userProfile, JSON.parse(saved));
  }
});
</script>

<style scoped>
/* 밝은 배경 + 진한 버튼 테마 */
:root {
  --bg: #f5f7fa;
  --panel: #ffffff;
  --accent: #1e3a8a;
  --accent2: #1e40af;
  --accent-dark: #0f172a;
  --good: #15803d;
  --warn: #ea580c;
  --bad: #dc2626;
  --text: #0f172a;
  --text-medium: #1e293b;
  --muted: #475569;
  --card: #f8fafc;
  --shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  --border-color: #cbd5e1;
  --primary-color: #1e3a8a;
  --background-color: #f8fafc;
  --container-bg: #ffffff;
  --text-dark: #1e293b;
  --text-light: #ffffff;
}

* {
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

.app {
  max-width: 560px;
  margin: 0 auto;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f0f3f6 0%, var(--bg) 100%);
}

/* 상단 바 */
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: max(10px, env(safe-area-inset-top)) 14px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: var(--panel);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow);
}

.app-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  object-fit: contain;
}

.title-col {
  display: flex;
  flex-direction: column;
}

.title-col b {
  font-size: clamp(16px, 4vw, 18px);
  color: var(--text);
  font-weight: 700;
}

.small {
  font-size: 12px;
  color: var(--muted);
}

.hud {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pill {
  padding: 6px 12px;
  border: 2px solid #1e293b;
  border-radius: 999px;
  color: white;
  font-size: 14px;
  font-weight: 800;
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  box-shadow: 0 2px 4px rgba(30, 58, 138, 0.4);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.xpbar {
  position: relative;
  height: 18px;
  background: #334155;
  border: 3px solid #0f172a;
  border-radius: 999px;
  overflow: hidden;
  width: 150px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5);
}

.xpbar > i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #10b981 50%, #fbbf24 100%);
  width: 0%;
  transition: width 0.3s;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.9), inset 0 2px 3px rgba(255, 255, 255, 0.4);
}

/* 콘텐츠 */
.content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  padding-bottom: 80px;
  flex-grow: 1;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.panel > .ph {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(to right, #f8f9fa, #e9ecef);
  font-weight: 700;
  font-size: 15px;
  color: var(--text);
}

.section {
  padding: 16px;
}

/* 업로드 */
.upload {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filebox {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px;
}

input[type="file"] {
  flex: 1;
  color: var(--text);
  font-weight: 600;
}

input[type="file"]::file-selector-button {
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  margin-right: 12px;
  box-shadow: 0 2px 8px rgba(30, 58, 138, 0.3);
  transition: all 0.2s;
}

input[type="file"]::file-selector-button:hover {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  box-shadow: 0 4px 12px rgba(30, 58, 138, 0.4);
}

.preview {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.preview img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 10px;
  border: 2px solid var(--accent);
}

input[type="text"],
input[type="number"] {
  width: 100%;
  background: white;
  border: 2px solid var(--border-color);
  border-radius: 10px;
  padding: 12px;
  color: var(--text);
  min-height: 48px;
  font-size: 14px;
  font-weight: 500;
}

input[type="text"]::placeholder,
input[type="number"]::placeholder {
  color: #999;
  font-weight: 400;
}

button {
  min-height: 50px;
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  border: none;
  border-radius: 12px;
  padding: 14px 20px;
  color: #ffffff;
  font-weight: 700;
  font-size: 15px;
  box-shadow: 0 4px 12px rgba(30, 58, 138, 0.4);
  transition: all 0.2s;
  cursor: pointer;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

button:hover:not(:disabled) {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(30, 58, 138, 0.5);
}

button:disabled {
  background: #64748b;
  color: #e2e8f0;
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.5;
}

.btn-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* 로그 */
.log {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 40vh;
  overflow-y: auto;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.msg .avatar-b {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--accent);
}

.bubble {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px;
  flex: 1;
  white-space: pre-wrap;
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 인벤토리 */
.inv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.inv-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  min-height: 85px;
}

.inv-card b {
  color: #0f172a;
  font-weight: 800;
  font-size: 17px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.inv-card .small {
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
}

.inv-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15);
  border-color: var(--accent);
}

.inv-card .badge {
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
  font-weight: 800;
  align-self: flex-start;
  box-shadow: 0 3px 6px rgba(15, 23, 42, 0.4);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.inv-card.expiring {
  border-color: var(--warn);
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  box-shadow: 0 2px 8px rgba(234, 88, 12, 0.2);
}

.inv-card.expiring .badge {
  background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
  box-shadow: 0 3px 6px rgba(194, 65, 12, 0.5);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.inv-card.expiring .small {
  color: #92400e;
  font-weight: 700;
}

.inv-card.expired {
  border-color: var(--bad);
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

.inv-card.expired .badge {
  background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%);
  box-shadow: 0 3px 6px rgba(185, 28, 28, 0.5);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.inv-card.expired .small {
  color: #7f1d1d;
  font-weight: 700;
}

/* 레시피 카드 */
.recipe-card {
  background: white;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  border-left: 5px solid var(--accent);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.recipe-card:hover {
  background: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* 퀘스트 카드 */
.quest-card {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 2px solid #fbbf24;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(251, 191, 36, 0.2);
  transition: all 0.2s;
}

.quest-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
}

.quest-header {
  margin-bottom: 8px;
}

.quest-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.quest-title b {
  font-size: 16px;
  color: #78350f;
  flex: 1;
}

.xp-badge {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 2px 4px rgba(249, 115, 22, 0.3);
  white-space: nowrap;
}

.quest-reason {
  color: #92400e;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.5;
}

.quest-checks {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 12px;
}

.check-item {
  color: #78350f;
  font-size: 13px;
  padding: 4px 0;
  font-weight: 500;
}

.quest-btn {
  width: 100%;
  min-height: 44px;
  background: linear-gradient(135deg, #15803d 0%, #16a34a 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(21, 128, 61, 0.3);
  transition: all 0.2s;
}

.quest-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #166534 0%, #15803d 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(21, 128, 61, 0.4);
}

.quest-btn:disabled {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  cursor: not-allowed;
  opacity: 0.7;
}

.quest-btn.completed {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

.rc-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rc-title b {
  font-size: 16px;
  color: var(--text);
  font-weight: 700;
}

.rc-meta {
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--text);
  list-style: none;
}

.rc-meta li {
  margin: 6px 0;
  font-weight: 500;
}

.rc-meta strong {
  color: var(--accent);
}

.detail-btn {
  width: 100%;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%) !important;
  font-size: 14px !important;
  min-height: 46px !important;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.4) !important;
}

.detail-btn:hover {
  background: linear-gradient(135deg, #000000 0%, #0f172a 100%) !important;
  box-shadow: 0 5px 14px rgba(15, 23, 42, 0.5) !important;
}

.nutrition-badge {
  background: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  margin-right: 6px;
  border: 2px solid var(--border-color);
  color: var(--text);
  font-weight: 600;
  display: inline-block;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 쇼핑 리스트 */
.shopping-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.shopping-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  text-decoration: none;
  color: var(--text);
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.shopping-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
  border-color: var(--accent);
}

.shopping-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.shopping-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shopping-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--text);
}

.shopping-qty {
  font-size: 12px;
  color: var(--muted);
  font-weight: 500;
}

.shopping-arrow {
  font-size: 20px;
  color: var(--accent);
  font-weight: 700;
  flex-shrink: 0;
}

/* 레시피 상세 뷰 */
.recipe-detail-view {
  padding: 20px 16px;
  background: #ffffff;
  min-height: 100vh;
  position: relative;
  max-width: 560px;
  margin: 0 auto;
  width: 100%;
}

.recipe-detail-view h2 {
  color: var(--text);
  margin-top: 0;
  font-weight: 700;
}

.recipe-detail-view h3 {
  color: var(--text);
  margin-top: 20px;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 8px;
  font-weight: 700;
}

.recipe-detail-view ul,
.recipe-detail-view ol {
  padding-left: 20px;
}

.recipe-detail-view li {
  margin-bottom: 10px;
  color: var(--text);
  font-weight: 500;
  line-height: 1.6;
}

.recipe-detail-view p {
  color: var(--text);
  font-weight: 500;
  line-height: 1.6;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.detail-meta span {
  background: white;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  border: 2px solid var(--border-color);
  color: var(--text);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.detail-section {
  margin-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 20px;
}

.detail-section:last-child {
  border-bottom: none;
}

.source-link {
  display: inline-block;
  padding: 10px 20px;
  background-color: var(--accent);
  color: var(--text-light);
  text-decoration: none;
  border-radius: 25px;
  font-weight: 500;
  transition: background-color 0.3s;
}

.source-link:hover {
  background-color: var(--accent2);
}

.back-button {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%) !important;
  margin-bottom: 20px;
  width: auto;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.4) !important;
}

.back-button:hover {
  background: linear-gradient(135deg, #000000 0%, #0f172a 100%) !important;
}

/* 프로필 폼 */
.profile-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-group input {
  padding: 14px 16px;
  border: 2px solid var(--border-color);
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
  background: white;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
}

.form-group input::placeholder {
  color: var(--muted);
  font-weight: 400;
}

.form-hint {
  font-size: 13px;
  color: var(--muted);
  font-weight: 500;
  margin-top: -4px;
}

.save-profile-btn {
  min-height: 54px;
  background: linear-gradient(135deg, #15803d 0%, #16a34a 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(21, 128, 61, 0.4);
  transition: all 0.2s;
  margin-top: 8px;
}

.save-profile-btn:hover {
  background: linear-gradient(135deg, #166534 0%, #15803d 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(21, 128, 61, 0.5);
}

.save-profile-btn:active {
  transform: translateY(0);
}

.save-success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 2px solid #10b981;
  color: #065f46;
  padding: 16px;
  border-radius: 10px;
  text-align: center;
  font-weight: 700;
  font-size: 15px;
  animation: slideIn 0.3s ease-out;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 챗봇 */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
  background-color: var(--container-bg);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.message-area {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: var(--background-color);
}

.message-wrapper {
  display: flex;
  max-width: 85%;
}

.message-wrapper.user {
  align-self: flex-end;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

.message-bubble {
  padding: 12px 18px;
  border-radius: 20px;
  color: var(--text-dark);
  line-height: 1.6;
  word-wrap: break-word;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.message-wrapper.user .message-bubble {
  background-color: var(--primary-color);
  color: var(--text-light);
  border-top-right-radius: 4px;
}

.message-wrapper.assistant .message-bubble {
  background-color: #e9e9eb;
  color: var(--text-dark);
  border-top-left-radius: 4px;
}

.message-bubble p {
  margin: 0;
}

.uploaded-image {
  max-width: 100%;
  border-radius: 15px;
  margin-top: 5px;
}

.input-area {
  display: flex;
  align-items: center;
  padding: 12px;
  border-top: 1px solid var(--border-color);
  background-color: var(--container-bg);
}

.file-upload-label {
  cursor: pointer;
  padding: 10px;
  font-size: 24px;
  color: #555;
  transition: color 0.2s;
}

.file-upload-label:hover {
  color: var(--primary-color);
}

#chat-file-upload {
  display: none;
}

.input-area input[type="text"] {
  flex-grow: 1;
  border: none;
  padding: 12px;
  border-radius: 20px;
  background-color: #f0f0f0;
  outline: none;
  font-size: 16px;
  margin: 0 8px;
}

.input-area input[type="text"]:focus {
  background-color: #e9e9e9;
}

.input-area button {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: var(--primary-color);
  min-height: auto;
  box-shadow: none;
}

.input-area button:disabled {
  color: #a0a0a0;
  cursor: not-allowed;
}

.input-area button svg {
  width: 24px;
  height: 24px;
}

.loading-bubble {
  padding: 18px;
}

.dot-flashing {
  position: relative;
  width: 10px;
  height: 10px;
  border-radius: 5px;
  background-color: #999;
  color: #999;
  animation: dot-flashing 1s infinite linear alternate;
  animation-delay: 0.5s;
}

.dot-flashing::before,
.dot-flashing::after {
  content: '';
  display: inline-block;
  position: absolute;
  top: 0;
}

.dot-flashing::before {
  left: -15px;
  width: 10px;
  height: 10px;
  border-radius: 5px;
  background-color: #999;
  color: #999;
  animation: dot-flashing 1s infinite alternate;
  animation-delay: 0s;
}

.dot-flashing::after {
  left: 15px;
  width: 10px;
  height: 10px;
  border-radius: 5px;
  background-color: #999;
  color: #999;
  animation: dot-flashing 1s infinite alternate;
  animation-delay: 1s;
}

@keyframes dot-flashing {
  0% {
    background-color: #999;
  }
  50%,
  100% {
    background-color: #ccc;
  }
}

/* 챗봇 내 레시피 버튼 */
:deep(.chat-recipe-btn) {
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  margin: 4px 0;
  display: inline-block;
  text-align: left;
  box-shadow: 0 2px 6px rgba(30, 58, 138, 0.3);
  transition: all 0.2s;
}

:deep(.chat-recipe-btn:hover) {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(30, 58, 138, 0.4);
}

/* 챗봇 내 쇼핑 링크 */
:deep(.chat-shopping-link) {
  display: inline-block;
  padding: 8px 14px;
  margin: 4px 0;
  background: white;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  color: var(--text);
  text-decoration: none;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.chat-shopping-link:hover) {
  background: var(--card);
  border-color: var(--accent);
  transform: translateX(4px);
}

/* 하단 네비게이션 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 20;
  max-width: 560px;
  margin: 0 auto;
  background: var(--panel);
  border-top: 1px solid var(--border-color);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-around;
  padding: 10px 0;
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #7a7a7a;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  padding: 5px 10px;
  font-weight: 600;
}

.nav-item.active {
  color: var(--accent);
  font-weight: 700;
}

.nav-item span {
  margin-top: 2px;
}

.nav-icon {
  font-size: 24px;
  margin-bottom: 2px;
}

/* 챗봇 내 레시피 상세보기 스타일 */
.recipe-detail-inline {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.close-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
}

.close-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.detail-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 12px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text);
}

.nutrition-info, .ingredients, .steps {
  margin-top: 20px;
}

.nutrition-info h4, .ingredients h4, .steps h4 {
  color: var(--text);
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 700;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.nutrition-grid span {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(22, 163, 74, 0.1) 100%);
  padding: 10px;
  border-radius: 8px;
  text-align: center;
  font-weight: 600;
  color: var(--text);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.ingredients ul, .steps ol {
  padding-left: 24px;
  color: var(--text);
}

.ingredients li, .steps li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.steps li {
  margin-bottom: 12px;
}
</style>
