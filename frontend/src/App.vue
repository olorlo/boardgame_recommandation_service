<template>
  <nav class="navbar">
    <a href="#" class="navbar-brand" @click.prevent="showMain">
      <i class="fa-solid fa-dice"></i> 뭐할게임?
    </a>
    <div class="navbar-links">
      <a href="#" :class="{ active: view === 'main' || view === 'recommend' }" @click.prevent="showRecommend">
        <i class="fa-solid fa-link"></i> 추천
      </a>
      <button type="button" :class="{ active: toolModal === 'penalty' }" @click="openToolModal('penalty')">
        <i class="fa-solid fa-circle-exclamation"></i> 벌칙
      </button>
      <button type="button" :class="{ active: toolModal === 'turn' }" @click="openToolModal('turn')">
        <i class="fa-solid fa-route"></i> 순서
      </button>
      <a href="/community/"><i class="fa-regular fa-comment"></i> 커뮤니티</a>
      <a href="/accounts/login/">로그인</a>
      <a href="/accounts/signup/">회원가입</a>
    </div>
  </nav>

  <main class="container">
    <section v-if="view === 'main'">
      <div style="margin-bottom: 3rem;">
        <i class="fa-solid fa-dice" style="font-size: 3rem; color: #a491bc;"></i>
        <h1>뭐할게임?</h1>
        <p class="subtitle">5명이서 할 건 없다고? 여기 있음</p>
      </div>

      <div class="hero-actions">
        <button class="btn btn-yellow" @click="showRecommend">
          <i class="fa-solid fa-dice-d20"></i> 게임 추천받기
        </button>
        <button class="btn btn-red" @click="openToolModal('penalty')">
          <i class="fa-solid fa-skull"></i> 벌칙 원판
        </button>
        <button class="btn btn-brown" @click="openToolModal('turn')">
          <i class="fa-solid fa-route"></i> 사다리 순서
        </button>
      </div>
    </section>

    <section v-else>
      <div style="margin-bottom: 2rem;">
        <h2 style="color: var(--primary-color);">오늘 뭐하지?</h2>
        <p class="subtitle">상황이나 조건으로 골라보기</p>
      </div>

      <div class="panels">
        <div class="card panel">
          <h3>상황 맞춤 AI 추천</h3>
          <div class="ai-row">
            <input
              v-model="situation"
              type="text"
              class="input-field"
              placeholder="예: 초보자 4명이서 1시간 안에 끝나는 파티 게임"
              style="margin-bottom: 0;"
              @keyup.enter="getAIRecommend"
            />
            <button class="btn btn-brown" style="margin: 0; width: 80px; padding: 0;" @click="getAIRecommend">
              추천
            </button>
          </div>
          <div v-if="aiLoading" style="text-align: center; margin-top: 10px;">
            <i class="fa-solid fa-spinner fa-spin"></i> AI가 고민 중...
          </div>
          <div style="margin-top: 20px;">
            <div v-for="item in aiRecommendations" :key="item.title" class="ai-item" @click="openAiRecommendModal(item.title)">
              <strong style="color: var(--primary-color); text-decoration: underline;">{{ item.title }}</strong><br />
              <span style="font-size: 0.9rem; color: var(--text-light);">{{ item.reason }}</span>
            </div>
            <p v-if="aiError" style="color: red;">오류: {{ aiError }}</p>
          </div>
        </div>

        <div class="card panel">
          <h3>조건 필터로 찾기</h3>
          <div class="filter-row">
            <input v-model="filters.players" type="number" placeholder="인원(명)" class="input-field" @change="fetchFilteredGames" @keyup.enter="fetchFilteredGames" />
            <input v-model="filters.time" type="number" placeholder="시간(분 이하)" class="input-field" @change="fetchFilteredGames" @keyup.enter="fetchFilteredGames" />
            <select v-model="filters.difficulty" class="input-field" @change="fetchFilteredGames">
              <option value="">난이도 전체</option>
              <option value="easy">쉬움</option>
              <option value="medium">보통</option>
              <option value="hard">어려움</option>
            </select>
          </div>
          <div v-if="filterLoading" style="text-align: center;">
            <i class="fa-solid fa-spinner fa-spin"></i> 검색 중...
          </div>
        </div>
      </div>

      <div class="games-grid">
        <div v-for="game in games" :key="game.game_id" class="card game-card" @click="openGameModal(game.game_id, game.title)">
          <h4>{{ game.title }}</h4>
          <p>순위: {{ game.rank }}</p>
          <p>출시: {{ game.released_year }}</p>
        </div>
      </div>

      <div style="margin-top: 2rem;">
        <button class="btn btn-outline" @click="showMain">메인으로 돌아가기</button>
      </div>
    </section>
  </main>

  <div v-if="toolModal" class="modal-overlay" @click.self="closeToolModal">
    <div class="modal-content tool-modal">
      <button class="modal-close" type="button" @click="closeToolModal">&times;</button>
      <div class="tool-tabs">
        <button class="tool-tab" :class="{ active: toolModal === 'penalty' }" @click="openToolModal('penalty')">
          <i class="fa-solid fa-circle-exclamation"></i> 벌칙
        </button>
        <button class="tool-tab" :class="{ active: toolModal === 'turn' }" @click="openToolModal('turn')">
          <i class="fa-solid fa-route"></i> 순서
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
        <p class="tool-subtitle">사람 이름을 등록한 뒤 사다리를 만들고 클릭해 첫 번째 순서를 뽑으세요.</p>

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

        <div v-if="ladderReady" class="ladder-wrap" @click="drawFirstTurn">
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
            <polyline v-if="ladderPathPoints" :points="ladderPathPoints" class="ladder-path" />
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
          <p class="ladder-hint">{{ ladderResult ? '다시 누르면 새로 뽑아요.' : '아무 사다리나 누르면 아래 사람이 공개돼요.' }}</p>
        </div>

        <div v-if="ladderResult" class="turn-result-text">{{ ladderResult }} 선턴!</div>
      </template>
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
const gameModal = reactive({
  open: false,
  loading: false,
  guideLoading: false,
  title: '',
  details: null,
  summary: '',
  youtubeVideoId: ''
})

const wheelColors = ['#c45b4c', '#e0ac5f', '#5d3f2e', '#6e9f84', '#6f88b8', '#a491bc', '#d7837f']
const ladderHeight = 260
const ladderMargin = 30
const wheelItems = ref([
  { id: 1, label: '설거지 하기', probability: 25, color: wheelColors[0] },
  { id: 2, label: '음료수 사기', probability: 25, color: wheelColors[1] },
  { id: 3, label: '뒷정리 하기', probability: 20, color: wheelColors[2] },
  { id: 4, label: '한 턴 쉬기', probability: 15, color: wheelColors[3] },
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
  fetchFilteredGames()
})

function showMain() {
  view.value = 'main'
}

function showRecommend() {
  view.value = 'recommend'
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
      headers: { 'Content-Type': 'application/json' },
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
  wheelItems.value.push({
    id: nextWheelId++,
    label: '새 벌칙',
    probability: 1,
    color: wheelColors[wheelItems.value.length % wheelColors.length]
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
  ladderReady.value = false
  ladderResult.value = ''
  ladderStartIndex.value = null
  ladderEndIndex.value = null
  ladderPath.value = []
  ladderBottomNames.value = []
}

function generateLadder() {
  if (playerNames.value.length < 2) {
    alert('이름을 2명 이상 등록해주세요.')
    return
  }

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
}

function drawFirstTurn() {
  if (!ladderReady.value || !ladderRows.value.length) return

  let position = Math.floor(Math.random() * playerNames.value.length)
  const startIndex = position
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
  ladderResult.value = ladderBottomNames.value[position]
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
    gameModal.summary = data.ai_summary || ''
    gameModal.youtubeVideoId = data.youtube_videoId || ''
  } finally {
    gameModal.loading = false
    gameModal.guideLoading = false
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
}
</script>
