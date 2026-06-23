<template>
  <nav class="navbar">
    <a href="#" class="navbar-brand" @click.prevent="showMain">
      <i class="fa-solid fa-dice"></i> 뭐할게임?
    </a>
    <div class="navbar-links">
      <a href="#" :class="{ active: view !== 'main' }" @click.prevent="showMain">
        <i class="fa-solid fa-home"></i> 메인
      </a>
      <button type="button" :class="{ active: toolModal === 'penalty' }" @click="openToolModal('penalty')">
        <i class="fa-solid fa-circle-exclamation"></i> 벌칙
      </button>
      <button type="button" :class="{ active: toolModal === 'turn' }" @click="openToolModal('turn')">
        <i class="fa-solid fa-route"></i> 순서
      </button>
      <a href="/community/"><i class="fa-regular fa-comment"></i> 낙서장</a>
      <template v-if="currentUser.isAuthenticated">
        <a :href="currentUser.profileUrl"><i class="fa-regular fa-user"></i> {{ currentUser.username }}</a>
        <form class="navbar-logout-form" @submit.prevent="logoutUser">
          <button type="submit">로그아웃</button>
        </form>
      </template>
      <template v-else>
        <a href="/accounts/login/">로그인</a>
        <a href="/accounts/signup/">회원가입</a>
      </template>
    </div>
  </nav>

  <main class="container">
    <section v-if="view === 'main'">
      <div style="margin-bottom: 3rem; position: relative;">
        <i class="fa-solid fa-dice" style="font-size: 3rem; color: #a491bc;"></i>
        <h1>뭐할게임?</h1>
        <p class="subtitle">5명이서 할 건 없다고? 여기 있음</p>
        <div style="margin-top: 10px; font-size: 0.8rem; color: #999;">※ 버그는 컨셉입니다.</div>
      </div>

      <div class="hero-actions" style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 1rem;">
        <button class="btn btn-yellow" @click="showAiRecommend" style="padding: 1.5rem 2rem; font-size: 1.2rem; width: 100%; max-width: 400px;">
          <i class="fa-solid fa-robot"></i> AI 상황 맞춤 추천
        </button>
        
        <button class="btn btn-blue" @click="showFilterSearch" style="padding: 1.5rem 2rem; font-size: 1.2rem; width: 100%; max-width: 400px;">
          <i class="fa-solid fa-filter"></i> 조건 필터로 직접 찾기
        </button>
      </div>
    </section>

    <section v-else-if="view === 'ai_recommend'">
      <div style="display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 2px solid var(--box-bg); padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: baseline; gap: 12px;">
          <h2 style="font-size: 1.8rem; color: var(--primary-color); margin: 0;">
            <i class="fa-solid fa-robot" style="color: var(--secondary-color);"></i> AI 맞춤 추천
          </h2>
          <span style="color: var(--text-light); font-size: 0.95rem;">상황을 알려주시면 가장 완벽한 게임을 찾아드려요</span>
        </div>
        <button @click="showMain" style="background: none; border: none; font-size: 1rem; color: var(--text-light); cursor: pointer; padding: 0; display: flex; align-items: center; gap: 5px;">
          <i class="fa-solid fa-arrow-left"></i> 메인으로
        </button>
      </div>

      <div style="display: grid; grid-template-columns: 320px 1fr; gap: 2rem; align-items: start;">
        <!-- Left: AI Input -->
        <div class="card panel" style="position: sticky; top: 2rem; aspect-ratio: 1 / 1; display: flex; flex-direction: column;">
          <h3 style="margin-top: 0; margin-bottom: 15px;">상황을 알려주세요</h3>
          <div style="display: flex; flex-direction: column; gap: 10px; flex-grow: 1;">
            <textarea
              v-model="situation"
              class="input-field"
              placeholder="예: 초보자 4명이서 1시간 안에 끝나는 파티 게임&#10;&#10;(Enter로 바로 검색, Shift+Enter로 줄바꿈)"
              style="flex-grow: 1; resize: none; margin-bottom: 0; border-radius: 8px;"
              @keydown.enter.exact.prevent="getAIRecommend"
            ></textarea>
            <button class="btn btn-brown" style="width: 100%; padding: 1rem; margin-top: 10px; font-size: 1.1rem;" @click="getAIRecommend" :disabled="aiLoading">
              <i class="fa-solid fa-wand-magic-sparkles"></i> AI에게 추천받기
            </button>
            <div v-if="aiLoading" style="text-align: center; margin-top: 10px; color: var(--primary-color);">
              <i class="fa-solid fa-spinner fa-spin"></i> AI가 고민 중...
            </div>
          </div>
        </div>

        <!-- Right: Recommendations -->
        <div>
          <div v-if="!aiLoading && aiRecommendations.length === 0" style="text-align: center; padding: 3rem; background: var(--box-bg); border-radius: 8px; border: 2px dashed #ccc;">
            <i class="fa-solid fa-robot" style="font-size: 3rem; color: #ccc; margin-bottom: 1rem;"></i>
            <p style="color: #666; font-size: 1.1rem; margin: 0;">어떤 상황인지 입력하고 Enter를 누르면<br>딱 맞는 게임을 추천해 드려요!</p>
          </div>
          <div v-else style="display: flex; flex-direction: column; gap: 15px;">
            <div v-for="item in aiRecommendations" :key="item.title" class="card ai-item" @click="openAiRecommendModal(item.title)" style="margin: 0;">
              <div class="ai-item-content" style="display: flex; gap: 15px; align-items: flex-start;">
                <img v-if="item.image_url" :src="item.image_url" alt="board game cover" class="ai-item-image" />
                <div class="ai-item-text" style="text-align: left;">
                  <strong style="color: var(--primary-color); text-decoration: underline; font-size: 1.1rem;">{{ item.title }}</strong><br />
                  <span style="font-size: 0.95rem; color: var(--text-dark); display: inline-block; margin-top: 5px;">{{ item.reason }}</span>
                </div>
              </div>
            </div>
            <p v-if="aiError" style="color: red; text-align: center;">오류: {{ aiError }}</p>
          </div>
        </div>
      </div>
    </section>

    <section v-else-if="view === 'filter_search'">
      <div style="display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 2px solid var(--box-bg); padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: baseline; gap: 12px;">
          <h2 style="font-size: 1.8rem; color: var(--primary-color); margin: 0;">
            <i class="fa-solid fa-filter" style="color: var(--secondary-color);"></i> 조건 필터 검색
          </h2>
          <span style="color: var(--text-light); font-size: 0.95rem;">인원, 시간, 난이도를 직접 지정해서 검색해보세요</span>
        </div>
        <button @click="showMain" style="background: none; border: none; font-size: 1rem; color: var(--text-light); cursor: pointer; padding: 0; display: flex; align-items: center; gap: 5px;">
          <i class="fa-solid fa-arrow-left"></i> 메인으로
        </button>
      </div>

      <div style="display: grid; grid-template-columns: 280px 1fr; gap: 2rem; align-items: start;">
        <!-- Left: Filters -->
        <div class="card panel" style="position: sticky; top: 2rem; aspect-ratio: 1 / 1; display: flex; flex-direction: column;">
          <h3 style="margin-top: 0; margin-bottom: 15px;">조건 필터</h3>
          <div style="display: flex; flex-direction: column; gap: 12px; flex-grow: 1;">
            <div>
              <label style="font-size: 0.9rem; color: var(--text-light); font-weight: bold;">인원(명)</label>
              <input v-model="filters.players" type="number" placeholder="예: 4" class="input-field" @keyup.enter="fetchFilteredGames" style="margin-bottom: 0;" />
            </div>
            <div>
              <label style="font-size: 0.9rem; color: var(--text-light); font-weight: bold;">시간(분 이하)</label>
              <input v-model="filters.time" type="number" placeholder="예: 60" class="input-field" @keyup.enter="fetchFilteredGames" style="margin-bottom: 0;" />
            </div>
            <div>
              <label style="font-size: 0.9rem; color: var(--text-light); font-weight: bold;">난이도</label>
              <select v-model="filters.difficulty" class="input-field" style="margin-bottom: 0;">
                <option value="">전체</option>
                <option value="easy">쉬움</option>
                <option value="medium">보통</option>
                <option value="hard">어려움</option>
              </select>
            </div>
            <div style="flex-grow: 1;"></div>
            <button class="btn btn-brown" style="margin-top: auto; width: 100%; padding: 0.8rem; font-size: 1rem;" @click="fetchFilteredGames" :disabled="filterLoading">
              <i class="fa-solid" :class="filterLoading ? 'fa-spinner fa-spin' : 'fa-search'"></i> 검색하기
            </button>
          </div>
        </div>

        <!-- Right: Results Table -->
        <div>
          <div v-if="!filterLoading && games.length === 0" style="text-align: center; padding: 3rem; background: var(--box-bg); border-radius: 8px; border: 2px dashed #ccc;">
            <i class="fa-solid fa-ghost" style="font-size: 3rem; color: #ccc; margin-bottom: 1rem;"></i>
            <p style="color: #666; font-size: 1.1rem; margin: 0;">조건에 맞는 게임이 없어요 😢<br>조건을 조금 바꿔보세요!</p>
          </div>
          <div v-else-if="games.length > 0" class="card" style="padding: 0; overflow: hidden;">
            <table class="games-table">
              <thead>
                <tr>
                  <th style="width: 80px; text-align: center;">순위</th>
                  <th>게임명</th>
                  <th style="width: 100px; text-align: center;">출시연도</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="game in games" :key="game.game_id" @click="openGameModal(game.game_id, game.title)">
                  <td style="text-align: center; font-weight: bold; color: var(--primary-color);">{{ game.rank }}</td>
                  <td>{{ game.title }}</td>
                  <td style="text-align: center; color: var(--text-light);">{{ game.released_year }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  </main>

  <div v-if="toolModal" class="modal-overlay" @click.self="closeToolModal">
    <div class="modal-content retro-window" style="padding: 3px;">
      <div class="retro-titlebar">
        <span id="retroModalTitle">
          <i v-if="toolModal === 'penalty'" class="fa-solid fa-skull"></i>
          <i v-else class="fa-solid fa-users"></i>
          {{ toolModal === 'penalty' ? '벌칙_프로그램.exe' : '순서_추첨기.exe' }}
        </span>
        <div class="retro-titlebar-close" @click="closeToolModal">X</div>
      </div>
      <div class="retro-content-inner">
        <div class="tool-tabs" style="margin-bottom:20px; text-align: left; display: block; border-bottom: none;">
          <button class="tool-tab" :style="toolModal === 'penalty' ? 'background: var(--primary-color); color: white; border: 2px inset #eadecc;' : 'background: #eadecc; color: var(--text-dark); border: 2px outset #fff;'" style="width:auto; padding:0.4rem 0.8rem; box-shadow:none; font-size:0.9rem; border-radius: 0; margin-right: 5px; cursor: pointer;" @click="openToolModal('penalty')">
            벌칙 뽑기
          </button>
          <button class="tool-tab" :style="toolModal === 'turn' ? 'background: var(--primary-color); color: white; border: 2px inset #eadecc;' : 'background: #eadecc; color: var(--text-dark); border: 2px outset #fff;'" style="width:auto; padding:0.4rem 0.8rem; box-shadow:none; font-size:0.9rem; border-radius: 0; cursor: pointer;" @click="openToolModal('turn')">
            순서 정하기
          </button>
        </div>

      <template v-if="toolModal === 'penalty'">
        <h2 class="tool-title">벌칙 원판</h2>
        <p class="tool-subtitle">벌칙과 확률을 정한 뒤 원판을 돌려보세요.</p>

        <div class="wheel-layout">
          <div class="wheel-stage">
            <div class="wheel-pointer"></div>
            <svg
              class="penalty-wheel"
              viewBox="0 0 300 300"
              role="img"
              aria-label="벌칙 원판"
            >
              <g class="wheel-rotor" :style="{ transform: `rotate(${wheelRotation}deg)` }">
                <g v-for="slice in wheelSlices" :key="slice.id">
                  <path
                    :d="slice.path"
                    :fill="slice.color"
                    class="wheel-slice"
                  />
                  <text
                    :x="slice.labelX"
                    :y="slice.labelY"
                    :transform="`rotate(${slice.textRotation} ${slice.labelX} ${slice.labelY})`"
                    class="wheel-svg-label"
                  >
                    <tspan
                      v-for="(line, lineIndex) in slice.labelLines"
                      :key="`${slice.id}-${lineIndex}`"
                      :x="slice.labelX"
                      :dy="lineIndex === 0 ? slice.firstLineDy : 14"
                    >
                      {{ line }}
                    </tspan>
                  </text>
                </g>
              </g>
              <circle cx="150" cy="150" r="42" class="wheel-center-circle" />
              <text x="150" y="155" text-anchor="middle" class="wheel-center-text">START</text>
            </svg>
          </div>

          <div class="wheel-controls">
            <div class="probability-total" :class="{ invalid: manualProbabilityTotal > 100 }">
              직접 설정 {{ manualProbabilityTotal }}% / 무사 통과 자동 {{ autoSafeProbability }}%
            </div>
            <div v-for="(item, index) in wheelItems" :key="item.id" class="wheel-item-row">
              <span class="color-dot" :style="{ background: item.color }"></span>
              <input v-model="item.label" class="input-field wheel-label" aria-label="벌칙 내용" />
              <input
                :value="item.isAuto ? autoSafeProbability : item.probability"
                :disabled="item.isAuto"
                @input="item.probability = Number($event.target.value)"
                type="number"
                min="0"
                max="100"
                step="1"
                class="input-field wheel-probability"
                aria-label="벌칙 확률"
              />
              <span class="percent-mark">%</span>
              <button class="icon-btn" type="button" @click="removeWheelItem(index)" :disabled="item.isAuto || wheelItems.length <= 2">
                <i class="fa-solid fa-trash"></i>
              </button>
            </div>
            <button class="btn btn-outline tool-small-btn" type="button" @click="addWheelItem">
              <i class="fa-solid fa-plus"></i> 벌칙 추가
            </button>
          </div>
        </div>

        <p v-if="wheelError" class="tool-error">{{ wheelError }}</p>
        <div v-if="penaltyResult" class="tool-result-text">결과: {{ penaltyResult }}</div>
        <button class="btn btn-red" :disabled="wheelSpinning" @click="spinPenaltyWheel">
          <i class="fa-solid fa-rotate"></i> {{ wheelSpinning ? '도는 중...' : '원판 돌리기' }}
        </button>
      </template>

      <template v-else>
        <h2 class="tool-title">사다리 순서 뽑기</h2>
        <p class="tool-subtitle">사람 이름을 등록한 뒤 사다리 위쪽 시작점을 눌러 첫 번째 순서를 뽑으세요.</p>

        <div class="name-entry">
          <input v-model="playerNameInput" class="input-field" placeholder="이름 입력" @keyup.enter="addPlayerName" />
          <button class="btn btn-brown name-add-btn" type="button" @click="addPlayerName">
            <i class="fa-solid fa-plus"></i> 추가
          </button>
        </div>

        <p v-if="!playerNames.length" class="tool-empty">아직 등록된 사람이 없습니다.</p>

        <div class="player-chip-list">
          <span v-for="(name, index) in playerNames" :key="name" class="player-chip">
            {{ name }}
            <button type="button" @click="removePlayerName(index)">&times;</button>
          </span>
        </div>

        <button class="btn btn-brown" type="button" @click="generateLadder">
          <i class="fa-solid fa-shuffle"></i> 사다리 만들기
        </button>

        <div v-if="ladderReady" class="ladder-wrap">
          <div class="ladder-start-row" :style="{ gridTemplateColumns: `repeat(${playerNames.length}, 1fr)` }">
            <button
              v-for="(_, index) in playerNames"
              :key="`start-${index}`"
              type="button"
              class="ladder-start-button"
              :class="{ active: ladderStartIndex === index && (ladderAnimating || ladderResult) }"
              @click="drawFirstTurn(index)"
            >
              <i class="fa-solid fa-arrow-down"></i>
              <span>시작</span>
            </button>
          </div>
          <svg class="ladder-svg" :viewBox="`0 0 ${ladderWidth} ${ladderHeight}`" role="img" aria-label="사다리">
            <line
              v-for="(_, index) in playerNames"
              :key="`rail-${index}`"
              :x1="ladderX(index)"
              y1="16"
              :x2="ladderX(index)"
              :y2="ladderHeight - 16"
              class="ladder-rail-line"
            />
            <line
              v-for="rung in ladderRungs"
              :key="rung.id"
              :x1="ladderX(rung.left)"
              :y1="ladderY(rung.row)"
              :x2="ladderX(rung.left + 1)"
              :y2="ladderY(rung.row)"
              class="ladder-rung-line"
            />
            <polyline v-if="ladderPathPoints" :key="ladderRunKey" :points="ladderPathPoints" class="ladder-path" />
          </svg>
          <div class="ladder-bottom" :style="{ gridTemplateColumns: `repeat(${playerNames.length}, 1fr)` }">
            <span
              v-for="(name, index) in ladderBottomNames"
              :key="`${name}-${index}`"
              :class="{ revealed: ladderResult && ladderEndIndex === index }"
            >
              {{ ladderResult && ladderEndIndex === index ? name : '?' }}
            </span>
          </div>
          <p class="ladder-hint">
            {{ ladderResult ? '위쪽 시작점을 다시 누르면 새로 뽑아요.' : '위쪽 시작 버튼을 누르면 아래 사람이 공개돼요.' }}
          </p>
        </div>

        <div v-if="ladderResult" class="turn-result-text">{{ ladderResult }} 선턴!</div>
      </template>
        <div style="margin-top: 15px; font-size: 0.75rem; color: var(--text-light); text-align: right;">※ 클릭은 자유, 결과는 책임 안 짐</div>
      </div>
    </div>
  </div>

  <!-- B-grade Retro Ads (Bottom Right) -->
  <div style="position: fixed; bottom: 20px; right: 20px; z-index: 999; display: flex; flex-direction: column; gap: 15px; pointer-events: none;">
      <!-- Ad 1: Penalty -->
      <div class="b-grade-ad" style="border: 3px outset #eadecc;" @click="openToolModal('penalty')">
          <div style="background: #fff; border: 2px inset #eadecc; padding: 10px 5px;">
              <div style="color: red; font-size: 0.75rem; font-weight: bold; margin-bottom: 4px; animation: blink 1s infinite;">[ 경 고 ]</div>
              <div style="color: var(--primary-color); font-size: 0.9rem; font-weight: 900; margin-bottom: 10px; line-height: 1.3;">☠ 벌칙 안 뽑고<br>도망갈거임?</div>
              <button style="background: var(--accent-color); color: white; border: 2px outset #eadecc; font-size: 0.85rem; font-weight: bold; width: 100%; padding: 4px 0; cursor: pointer; box-shadow: none;">벌칙 룰렛 ➔</button>
          </div>
      </div>

      <!-- Ad 2: Turn -->
      <div class="b-grade-ad" style="border: 3px dashed var(--secondary-color);" @click="openToolModal('turn')">
          <div style="background: #fff; padding: 8px 5px; border: 1px solid var(--secondary-color);">
              <div style="color: var(--primary-color); font-size: 0.9rem; font-weight: 900; margin-bottom: 10px; line-height: 1.3;">🪜 순서 정하고<br>보드게임하자!</div>
              <button style="background: var(--secondary-color); color: #fff; border: 2px outset #eadecc; font-size: 0.85rem; font-weight: bold; width: 100%; padding: 4px 0; cursor: pointer; box-shadow: none;">순서 정하기 ➔</button>
          </div>
      </div>
  </div>

  <div v-if="gameModal.open" class="modal-overlay" @click.self="closeGameDetail">
    <div class="modal-content wide">
      <button class="modal-close" type="button" @click="closeGameDetail">&times;</button>
      <h2 style="color: var(--primary-color); margin-bottom: 5px;">{{ gameModal.title }}</h2>
      <div v-if="gameModal.loading"><i class="fa-solid fa-spinner fa-spin"></i> 게임 정보를 불러오는 중...</div>
      <div v-else style="text-align: left;">
        <div class="detail-grid" style="margin-top: 20px;">
          <div style="flex: 1;">
            <div v-if="gameModal.details">
              <h4>기본 정보</h4>
              <p>인원: {{ gameModal.details.min_players }} ~ {{ gameModal.details.max_players }}명</p>
              <p>시간: {{ gameModal.details.playing_time }}분</p>
              <p>난이도: {{ Number(gameModal.details.weight).toFixed(1) }} / 5.0</p>
            </div>

            <h4 style="margin-top: 20px; color: var(--accent-color);">AI 룰 요약</h4>
            <div style="background: var(--box-bg); padding: 10px; border-radius: 8px; font-size: 0.9rem; white-space: pre-line;">
              <i v-if="gameModal.guideLoading" class="fa-solid fa-spinner fa-spin"></i>
              {{ gameModal.summary || (gameModal.guideLoading ? '요약 중...' : '요약을 불러오지 못했습니다.') }}
            </div>
          </div>
          <div style="flex: 1;">
            <h4>유튜브 영상 (룰 가이드)</h4>
            <div class="youtube-box">
              <i v-if="gameModal.guideLoading" class="fa-solid fa-spinner fa-spin"></i>
              <iframe
                v-else-if="gameModal.youtubeVideoId"
                width="100%"
                height="100%"
                :src="`https://www.youtube.com/embed/${gameModal.youtubeVideoId}`"
                frameborder="0"
                allowfullscreen
                style="border-radius: 8px;"
              ></iframe>
              <span v-else>영상 없음</span>
            </div>
          </div>
        </div>

        <div class="community-share-box" style="margin-top: 20px; padding: 15px; background: var(--box-bg); border-radius: 8px;">
          <h4 style="margin-top: 0; margin-bottom: 10px; color: var(--primary-color);">낙서장에 공유하기</h4>
          <textarea v-model="gameModal.shareContent" class="input-field" placeholder="이 게임 어땠나요? 추천받은 소감이나 리뷰를 남겨보세요!" style="width: 100%; min-height: 80px; resize: vertical; margin-bottom: 10px;"></textarea>
          <div style="text-align: right;">
             <button class="btn btn-yellow" style="margin: 0; width: auto; font-size: 0.9rem; padding: 0.5rem 1rem;" @click="shareToCommunity" :disabled="gameModal.shareLoading">
               <i class="fa-solid fa-paper-plane"></i> {{ gameModal.shareLoading ? '공유 중...' : '낙서장에 등록' }}
             </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const view = ref('main')
const games = ref([])
const filters = reactive({ players: '', time: '', difficulty: '' })
const filterLoading = ref(false)
const situation = ref('')
const aiLoading = ref(false)
const aiError = ref('')
const aiRecommendations = ref([])
const currentUser = reactive({
  isAuthenticated: false,
  username: '',
  profileUrl: ''
})
const toolModal = ref('')
const penaltyResult = ref('')
const wheelRotation = ref(0)
const wheelSpinning = ref(false)
const wheelError = ref('')
const playerNameInput = ref('')
const playerNames = ref([])
const ladderRows = ref([])
const ladderReady = ref(false)
const ladderResult = ref('')
const ladderStartIndex = ref(null)
const ladderEndIndex = ref(null)
const ladderPath = ref([])
const ladderBottomNames = ref([])
const ladderAnimating = ref(false)
const ladderRunKey = ref(0)
let ladderTimer = null
const gameModal = reactive({
  open: false,
  loading: false,
  guideLoading: false,
  title: '',
  details: null,
  summary: '',
  youtubeVideoId: '',
  shareContent: '',
  shareLoading: false
})

const wheelColors = ['#c45b4c', '#e0ac5f', '#5d3f2e', '#6e9f84', '#6f88b8', '#a491bc', '#d7837f']
const ladderHeight = 260
const ladderMargin = 30
const wheelItems = ref([
  { id: 1, label: '꿀밤 맞기', probability: 25, color: wheelColors[0] },
  { id: 2, label: '커피 사기', probability: 25, color: wheelColors[1] },
  { id: 3, label: '뒷정리 하기', probability: 20, color: wheelColors[2] },
  { id: 4, label: '10분간 말 못하기 ', probability: 15, color: wheelColors[3] },
  { id: 5, label: '무사 통과', probability: 15, color: wheelColors[4], isAuto: true }
])
let nextWheelId = 6

const manualProbabilityTotal = computed(() => {
  return wheelItems.value
    .filter((item) => !item.isAuto)
    .reduce((sum, item) => sum + normalizePercent(item.probability), 0)
})
const autoSafeProbability = computed(() => Math.max(0, 100 - manualProbabilityTotal.value))
const adjustedWheelItems = computed(() => {
  return wheelItems.value.map((item) => ({
    ...item,
    probability: item.isAuto ? autoSafeProbability.value : normalizePercent(item.probability)
  }))
})

const wheelSlices = computed(() => {
  let cursor = 0
  return adjustedWheelItems.value
    .filter((item) => item.label.trim() && normalizePercent(item.probability) > 0)
    .map((item) => {
      const amount = normalizePercent(item.probability)
      const startAngle = cursor * 3.6 - 90
      const endAngle = (cursor + amount) * 3.6 - 90
      const centerAngle = startAngle + (endAngle - startAngle) / 2
      cursor += amount
      const labelPoint = polarToCartesian(150, 150, 92, centerAngle)
      const labelLines = splitWheelLabel(item.label.trim())
      return {
        id: item.id,
        color: item.color,
        path: describeArcSlice(150, 150, 138, startAngle, endAngle),
        labelX: labelPoint.x,
        labelY: labelPoint.y,
        textRotation: centerAngle + 90,
        labelLines,
        firstLineDy: labelLines.length > 1 ? -6 : 4
      }
    })
})

const ladderWidth = computed(() => Math.max(280, (playerNames.value.length - 1) * 86 + ladderMargin * 2))
const ladderRungs = computed(() => {
  return ladderRows.value.flatMap((row, rowIndex) => row.map((left) => ({ id: `${rowIndex}-${left}`, row: rowIndex, left })))
})
const ladderPathPoints = computed(() => ladderPath.value.map((point) => `${point.x},${point.y}`).join(' '))

onMounted(() => {
  fetchCurrentUser()
  fetchFilteredGames()
  openInitialToolFromUrl()
})

function showMain() {
  view.value = 'main'
}

function showAiRecommend() {
  view.value = 'ai_recommend'
}

function showFilterSearch() {
  view.value = 'filter_search'
  if (!games.value.length) fetchFilteredGames()
}

async function fetchFilteredGames() {
  filterLoading.value = true
  const params = new URLSearchParams()
  if (filters.players) params.append('players', filters.players)
  if (filters.time) params.append('time', filters.time)
  if (filters.difficulty) params.append('difficulty', filters.difficulty)

  try {
    const response = await fetch(`/boardgames/filter/?${params.toString()}`)
    const data = await response.json()
    games.value = data.games || []
  } finally {
    filterLoading.value = false
  }
}

async function getAIRecommend() {
  if (!situation.value) {
    alert('상황을 입력해주세요.')
    return
  }

  aiLoading.value = true
  aiError.value = ''
  aiRecommendations.value = []

  try {
    const response = await fetch('/boardgames/recommend/', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ situation: situation.value })
    })
    const data = await response.json()
    if (data.error) {
      aiError.value = data.error
      return
    }
    aiRecommendations.value = data.recommendations || []
  } catch (error) {
    aiError.value = error.message
  } finally {
    aiLoading.value = false
  }
}

function openToolModal(type) {
  toolModal.value = type
}

function closeToolModal() {
  toolModal.value = ''
}

async function fetchCurrentUser() {
  try {
    const response = await fetch('/accounts/me/', { credentials: 'same-origin' })
    const data = await response.json()
    currentUser.isAuthenticated = Boolean(data.is_authenticated)
    currentUser.username = data.username || ''
    currentUser.profileUrl = data.profile_url || ''
  } catch {
    currentUser.isAuthenticated = false
  }
}

async function logoutUser() {
  await fetch('/accounts/logout/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': getCookie('csrftoken')
    }
  })
  window.location.href = '/'
}

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(';') : []
  for (const cookie of cookies) {
    const trimmed = cookie.trim()
    if (trimmed.startsWith(`${name}=`)) {
      return decodeURIComponent(trimmed.slice(name.length + 1))
    }
  }
  return ''
}

function normalizePercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.min(100, Math.round(number)))
}

function polarToCartesian(cx, cy, radius, angleInDegrees) {
  const angleInRadians = (angleInDegrees * Math.PI) / 180
  return {
    x: cx + radius * Math.cos(angleInRadians),
    y: cy + radius * Math.sin(angleInRadians)
  }
}

function describeArcSlice(cx, cy, radius, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, radius, startAngle)
  const end = polarToCartesian(cx, cy, radius, endAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  return [
    `M ${cx} ${cy}`,
    `L ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`,
    'Z'
  ].join(' ')
}

function splitWheelLabel(label) {
  if (label.length <= 5) return [label]
  const words = label.split(/\s+/).filter(Boolean)
  if (words.length > 1) {
    const lines = []
    let line = ''
    words.forEach((word) => {
      const nextLine = line ? `${line} ${word}` : word
      if (nextLine.length > 5 && line) {
        lines.push(line)
        line = word
      } else {
        line = nextLine
      }
    })
    if (line) lines.push(line)
    return lines.slice(0, 2)
  }
  return [label.slice(0, 5), label.slice(5, 10)].filter(Boolean)
}

function addWheelItem() {
  const autoIndex = wheelItems.value.findIndex((item) => item.isAuto)
  const insertIndex = autoIndex === -1 ? wheelItems.value.length : autoIndex
  wheelItems.value.splice(insertIndex, 0, {
    id: nextWheelId++,
    label: '새 벌칙',
    probability: 1,
    color: wheelColors[insertIndex % wheelColors.length]
  })
}

function removeWheelItem(index) {
  if (wheelItems.value.length <= 2) return
  wheelItems.value.splice(index, 1)
}

function spinPenaltyWheel() {
  if (wheelSpinning.value) return
  wheelError.value = ''
  penaltyResult.value = ''

  const validItems = adjustedWheelItems.value.filter((item) => item.label.trim() && normalizePercent(item.probability) > 0)
  if (validItems.length < 2) {
    wheelError.value = '벌칙을 2개 이상 입력해주세요.'
    return
  }
  if (manualProbabilityTotal.value > 100) {
    wheelError.value = '무사 통과를 제외한 확률 합계가 100%를 넘지 않게 조정해주세요.'
    return
  }

  const randomPoint = Math.random() * 100
  let cursor = 0
  let selected = validItems[0]
  let selectedStart = 0

  for (const item of validItems) {
    const amount = normalizePercent(item.probability)
    if (randomPoint >= cursor && randomPoint < cursor + amount) {
      selected = item
      selectedStart = cursor
      break
    }
    cursor += amount
  }

  const selectedCenterAngle = (selectedStart + normalizePercent(selected.probability) / 2) * 3.6
  const currentAngle = ((wheelRotation.value % 360) + 360) % 360
  const landingDelta = (360 - selectedCenterAngle - currentAngle + 360) % 360

  wheelSpinning.value = true
  wheelRotation.value += 1440 + landingDelta
  window.setTimeout(() => {
    penaltyResult.value = selected.label
    wheelSpinning.value = false
  }, 4300)
}

function addPlayerName() {
  const name = playerNameInput.value.trim()
  if (!name) return
  if (!playerNames.value.includes(name)) playerNames.value.push(name)
  playerNameInput.value = ''
  resetLadder()
}

function removePlayerName(index) {
  playerNames.value.splice(index, 1)
  resetLadder()
}

function resetLadder() {
  if (ladderTimer) window.clearTimeout(ladderTimer)
  ladderTimer = null
  ladderReady.value = false
  ladderResult.value = ''
  ladderStartIndex.value = null
  ladderEndIndex.value = null
  ladderPath.value = []
  ladderBottomNames.value = []
  ladderAnimating.value = false
}

function generateLadder() {
  if (playerNames.value.length < 2) {
    alert('이름을 2명 이상 등록해주세요.')
    return
  }
  if (ladderTimer) window.clearTimeout(ladderTimer)
  ladderTimer = null

  const rowCount = Math.max(6, playerNames.value.length * 2)
  const rows = []
  for (let row = 0; row < rowCount; row++) {
    const rungs = []
    let column = 0
    while (column < playerNames.value.length - 1) {
      if (Math.random() > 0.56) {
        rungs.push(column)
        column += 2
      } else {
        column += 1
      }
    }
    rows.push(rungs)
  }

  ladderRows.value = rows
  ladderBottomNames.value = shuffleNames(playerNames.value)
  ladderReady.value = true
  ladderResult.value = ''
  ladderStartIndex.value = null
  ladderEndIndex.value = null
  ladderPath.value = []
  ladderAnimating.value = false
}

function drawFirstTurn(startIndex) {
  if (!ladderReady.value || !ladderRows.value.length) return
  if (ladderAnimating.value) return
  if (startIndex < 0 || startIndex >= playerNames.value.length) return
  if (ladderTimer) window.clearTimeout(ladderTimer)

  let position = startIndex
  const path = [{ x: ladderX(position), y: 16 }]

  ladderRows.value.forEach((row, rowIndex) => {
    const y = ladderY(rowIndex)
    path.push({ x: ladderX(position), y })
    if (row.includes(position)) {
      position += 1
      path.push({ x: ladderX(position), y })
    } else if (row.includes(position - 1)) {
      position -= 1
      path.push({ x: ladderX(position), y })
    }
  })

  path.push({ x: ladderX(position), y: ladderHeight - 16 })
  ladderStartIndex.value = startIndex
  ladderEndIndex.value = position
  ladderPath.value = path
  ladderRunKey.value += 1
  ladderResult.value = ''
  ladderAnimating.value = true

  const result = ladderBottomNames.value[position]
  ladderTimer = window.setTimeout(() => {
    ladderResult.value = result
    ladderAnimating.value = false
    ladderTimer = null
  }, 700)
}

function openInitialToolFromUrl() {
  const params = new URLSearchParams(window.location.search)
  const tool = params.get('tool')
  if (tool === 'penalty' || tool === 'turn') {
    openToolModal(tool)
    window.history.replaceState({}, '', window.location.pathname)
  }
}

function shuffleNames(names) {
  const arr = [...names]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

function ladderX(index) {
  if (playerNames.value.length <= 1) return ladderWidth.value / 2
  const gap = (ladderWidth.value - ladderMargin * 2) / (playerNames.value.length - 1)
  return ladderMargin + index * gap
}

function ladderY(rowIndex) {
  if (ladderRows.value.length <= 1) return ladderHeight / 2
  const gap = (ladderHeight - 60) / (ladderRows.value.length - 1)
  return 30 + rowIndex * gap
}

async function openGameModal(gameId, title) {
  resetGameModal(title)
  gameModal.loading = true

  try {
    const response = await fetch(`/boardgames/api/${gameId}/details/`)
    if (!response.ok) throw new Error('Details not found')
    gameModal.details = await response.json()
    gameModal.loading = false
    fetchGameSmartGuide(gameId)
  } catch {
    gameModal.loading = false
    gameModal.summary = '상세 정보가 데이터베이스에 없습니다.'
  }
}

async function fetchGameSmartGuide(gameId) {
  gameModal.guideLoading = true
  try {
    const response = await fetch(`/boardgames/${gameId}/recommend/`)
    const data = await response.json()
    gameModal.summary = data.summary || ''
    gameModal.youtubeVideoId = data.youtube_videoId || ''
  } finally {
    gameModal.guideLoading = false
  }
}

async function openAiRecommendModal(title) {
  resetGameModal(`${title} (AI 추천)`)
  gameModal.loading = true
  gameModal.guideLoading = true

  try {
    const response = await fetch(`/boardgames/api/details_by_title/?title=${encodeURIComponent(title)}`)
    const data = await response.json()
    gameModal.details = data.details || null
    gameModal.summary = data.ai_summary || ''
    gameModal.youtubeVideoId = data.youtube_videoId || ''
  } finally {
    gameModal.loading = false
    gameModal.guideLoading = false
  }
}


async function shareToCommunity() {
  if (!gameModal.shareContent.trim()) {
    alert('내용을 입력해주세요.');
    return;
  }
  gameModal.shareLoading = true;
  try {
    let cleanTitle = gameModal.title.replace(' (AI 추천)', '').trim();
    const response = await fetch('/community/api/create/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        content: gameModal.shareContent,
        game_title: cleanTitle
      })
    });
    
    if (response.status === 401) {
       alert('로그인이 필요합니다. 로그인 페이지로 이동합니다.');
       window.location.href = '/accounts/login/';
       return;
    }
    
    const data = await response.json();
    if (data.status === 'success') {
      alert('낙서장에 성공적으로 공유되었습니다!');
      gameModal.shareContent = '';
    } else {
      alert(data.message || '공유에 실패했습니다.');
    }
  } catch (err) {
    alert('오류가 발생했습니다: ' + err.message);
  } finally {
    gameModal.shareLoading = false;
  }
}

function closeGameDetail() {
  gameModal.open = false
}

function resetGameModal(title) {
  gameModal.open = true
  gameModal.title = title
  gameModal.details = null
  gameModal.summary = ''
  gameModal.youtubeVideoId = ''
  gameModal.shareContent = ''
  gameModal.shareLoading = false
}
</script>
