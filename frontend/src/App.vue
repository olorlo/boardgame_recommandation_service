<template>
  <BoardBackground />
  <nav class="retro-titlebar-nav">
    <a href="#" class="navbar-brand" @click.prevent="showMain">
      <i class="fa-solid fa-dice"></i> 뭐할게임?
    </a>
    <div class="navbar-links">
      <a href="#" class="retro-btn blue" @click.prevent="showMain">
        <i class="fa-solid fa-home"></i> 메인
      </a>
      <a href="/community/" class="retro-btn green"><i class="fa-regular fa-comment"></i> 낙서장</a>
      <template v-if="currentUser.isAuthenticated">
        <a :href="currentUser.profileUrl" class="retro-btn yellow"><i class="fa-regular fa-user"></i> {{ currentUser.username }}</a>
        <form class="navbar-logout-form" @submit.prevent="logoutUser">
          <button type="submit" class="retro-btn red">로그아웃</button>
        </form>
      </template>
      <template v-else>
        <a href="/accounts/login/" class="retro-btn yellow">로그인</a>
        <a href="/accounts/signup/" class="retro-btn red">회원가입</a>
      </template>
    </div>
  </nav>

  <main class="container">
    <section v-if="view === 'main'">
      <div class="board-map-container">
        <!-- SVG 궤적 복구 (그리드 반응형에 맞춰 배경처럼 늘어남) -->
        <svg class="map-track-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
          <path d="M 90 10 C 70 5, 20 0, 20 20 C 20 45, 50 35, 50 50 C 50 70, 20 65, 20 80 C 20 95, 60 85, 80 85" 
                fill="none" stroke="var(--primary-color)" stroke-width="0.8" stroke-dasharray="2 2" stroke-linecap="round" opacity="0.6"/>
        </svg>

        <!-- 1. Start (뭐할게임?) -->
        <div class="map-tile tile-start">
          <div class="tile-content">
            <h2 class="start-title">START<br><span style="font-size:1.5rem">뭐할게임?</span></h2>
          </div>
        </div>

        <!-- 3. 최근 추천 (최근 본 게임) -->
        <div class="map-tile tile-recent">
          <div class="tile-header" style="justify-content: space-between;">
            <h3><i class="fa-solid fa-clock-rotate-left"></i> 최근 본 게임</h3>
            <button v-if="recentViewedGames.length" type="button" @click.stop="deleteCurrentRecentGame" style="font-size:0.85rem; padding: 4px 8px; border-radius: 4px; background: transparent; border: none; color: white; cursor: pointer;" title="현재 게임 기록 삭제">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
          <div class="tile-content" style="padding: 0; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative;">
            <p v-if="!recentViewedGames.length" class="recent-empty" style="font-size: 1.1rem; color: #888; text-align: center; padding: 20px;">아직 확인한 게임이 없습니다.</p>
            <div v-else class="carousel-container" style="display: flex; align-items: center; justify-content: space-between; width: 100%; height: 100%;">
              <button class="carousel-btn" @click.stop="prevRecentGame" :disabled="recentViewedGames.length <= 1" style="position: absolute; left: 8px; z-index: 10; background: rgba(255,255,255,0.85); border: none; border-radius: 50%; width: 32px; height: 32px; display: flex; justify-content: center; align-items: center; font-size: 1.1rem; color: var(--primary-color); cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" :style="{ opacity: recentViewedGames.length <= 1 ? 0.3 : 1 }">
                <i class="fa-solid fa-chevron-left"></i>
              </button>
              
              <div class="carousel-item" @click="openAiRecommendModal(currentRecentGame.title)" style="flex: 1; height: 100%; display: flex; flex-direction: column; cursor: pointer; transition: transform 0.2s; overflow: hidden; padding: 10px; box-sizing: border-box;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                
                <div class="carousel-image-container" style="flex: 1; min-height: 0; width: 100%; background-color: #f9f5ec; border-radius: 8px; display: flex; justify-content: center; align-items: center; overflow: hidden; margin-bottom: 8px;">
                  <img v-if="currentRecentGame.imageUrl" :src="currentRecentGame.imageUrl" alt="게임 썸네일" style="width: 100%; height: 100%; object-fit: contain;" />
                  <i v-else class="fa-solid fa-chess-board carousel-fallback-icon" style="font-size: 3rem; color: #d0c0a0;"></i>
                </div>
                
                <div style="text-align: center; padding-bottom: 2px;">
                  <div style="font-size: 1.1rem; font-weight: 900; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 5px;">
                    {{ currentRecentGame.title }}
                  </div>
                  <div style="font-size: 0.85rem; font-weight: bold; color: var(--primary-color); margin-top: 4px;">
                    자세히 보기 <i class="fa-solid fa-arrow-right"></i>
                  </div>
                </div>
                <div style="text-align: center; font-size: 0.7rem; color: #aaa; margin-top: 2px;">
                  {{ currentRecentIndex + 1 }} / {{ recentViewedGames.length }}
                </div>
              </div>
              
              <button class="carousel-btn" @click.stop="nextRecentGame" :disabled="recentViewedGames.length <= 1" style="position: absolute; right: 8px; z-index: 10; background: rgba(255,255,255,0.85); border: none; border-radius: 50%; width: 32px; height: 32px; display: flex; justify-content: center; align-items: center; font-size: 1.1rem; color: var(--primary-color); cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" :style="{ opacity: recentViewedGames.length <= 1 ? 0.3 : 1 }">
                <i class="fa-solid fa-chevron-right"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 4. 마법의 추천 칸 (Main CTA) -->
        <div class="map-tile tile-magic" @click="openRecommendInputModal">
          <div class="tile-content magic-content">
             <i class="fa-solid fa-wand-magic-sparkles giant-icon"></i>
             <h2>보드게임 추천받기</h2>
             <p>AI가 완벽한 게임을<br>찾아드립니다</p>
             <div class="click-indicator">클릭!</div>
          </div>
        </div>

        <!-- 5. 보드게임 순위 (전체 랭킹 활용) -->
        <div class="map-tile tile-ranking" style="cursor: pointer;" @click="openRankingModal">
          <div class="tile-header">
            <h3><i class="fa-solid fa-trophy" style="color: gold;"></i> 보드게임 순위</h3>
          </div>
          <div class="tile-content" style="padding: 10px; height: 100%;">
            <table class="games-table" style="margin: 0; width: 100%;">
              <thead>
                <tr style="border-bottom: 2px solid var(--primary-color);">
                  <th style="width: 40px; text-align: center; padding-bottom: 5px; font-size: 0.9rem;">순위</th>
                  <th style="text-align: left; padding-bottom: 5px; font-size: 0.9rem;">게임명</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="game in top5Games" :key="game.game_id" @click="openGameModal(game.game_id, game.title)" style="cursor: pointer;">
                  <td style="text-align: center; font-weight: bold; padding: 8px 0;" :style="{ color: game.rank <= 3 ? 'red' : 'var(--text-light)' }">{{ game.rank }}</td>
                  <td style="font-weight: bold; padding: 8px 0;">
                    <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; display: inline-block;">{{ game.title }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div style="text-align: center; margin-top: 10px; font-size: 0.85rem; color: var(--primary-color);">전체 순위 보기 <i class="fa-solid fa-arrow-pointer"></i></div>
          </div>
        </div>

      <!-- Trending Section -->
          <div class="trending-section" style="max-width: 800px; margin: 0 auto; text-align: left;">
            <h3 style="border-bottom: 2px solid var(--primary-color); padding-bottom: 10px; margin-bottom: 15px;">
              <i class="fa-solid fa-fire" style="color: red;"></i> 실시간 많이 찾는 보드게임
            </h3>

            <div v-if="trendingLoading" style="text-align: center; padding: 20px;"><i class="fa-solid fa-spinner fa-spin"></i> 불러오는 중...</div>
            <div v-else class="card" style="padding: 0; overflow: hidden;">
              <table class="games-table" style="margin: 0;">
                <tbody>
                  <tr v-for="game in visibleTrendingGames" :key="game.game_id + '-' + game.rank" @click="openGameModal(game.game_id, displayGameTitle(game))">
                    <td style="width: 50px; text-align: center; font-weight: bold; font-size: 1.1rem;" :style="{ color: game.rank <= 3 ? 'red' : 'var(--text-light)' }">{{ game.rank }}</td>
                    <td style="font-weight: bold; position: relative;">
                      <transition name="ticker-slide" mode="out-in">
                        <div :key="game.game_id" style="display: flex; align-items: center; gap: 8px; width: 100%;">
                          <span>{{ displayGameTitle(game) }}</span>
                          <span style="font-size: 0.85rem; color: var(--text-light); font-weight: normal;">
                            <i class="fa-regular fa-eye"></i> {{ game.view_count || 0 }}
                          </span>
                        </div>
                      </transition>
                    </td>
                    <td style="width: 50px; text-align: right; color: var(--text-light); padding-right: 20px; cursor: pointer;" @click.stop="showAllTrending = !showAllTrending">
                      <i v-if="!showAllTrending || game.rank === 1" class="fa-solid" :class="showAllTrending ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 7. 벌칙 뽑기 -->
        <div class="map-tile tile-tool-penalty" @click="openToolModal('penalty')">
          <div class="tile-content tool-content">
            <div class="tool-emoji">💣</div>
            <h3>벌칙 뽑기</h3>
          </div>
        </div>

        <!-- 장식용 더미 칸들 -->
        <div class="map-deco deco-1"><i class="fa-solid fa-dice"></i></div>
        <div class="map-deco deco-2"><i class="fa-solid fa-question"></i></div>
        <div class="map-deco deco-3"><i class="fa-solid fa-star"></i></div>
        <div class="map-deco deco-4"><i class="fa-solid fa-chess-knight"></i></div>
        <div class="map-deco deco-5"><i class="fa-solid fa-puzzle-piece"></i></div>

        <!-- 배경 주사위 (그리드 빈칸 배치) -->
        <div class="grid-bg-dice grid-dice-1"><i class="fa-solid fa-dice-one"></i></div>
        <div class="grid-bg-dice grid-dice-2"><i class="fa-solid fa-dice-two"></i></div>
        <div class="grid-bg-dice grid-dice-3"><i class="fa-solid fa-dice-three"></i></div>
        <div class="grid-bg-dice grid-dice-4"><i class="fa-solid fa-dice-four"></i></div>
        <div class="grid-bg-dice grid-dice-5"><i class="fa-solid fa-dice-five"></i></div>

      </div>
    </section>
  </main>

  <!-- Recommend Modals -->
  <div v-if="recommendModal.step > 0" class="modal-overlay" @click.self="closeRecommendModal">
    <div class="modal-content retro-window" style="padding: 3px; max-width: 600px; width: 100%;">
      <div class="retro-titlebar">
        <span><i class="fa-solid fa-wand-magic-sparkles"></i> AI_보드게임_추천.exe</span>
        <div class="retro-titlebar-close" @click="closeRecommendModal">X</div>
      </div>
      
      <div class="retro-content-inner" style="padding: 20px;">
        <!-- Step 1: Input -->
        <template v-if="recommendModal.step === 1">
          <h2 style="color: var(--primary-color); margin-bottom: 5px; text-align: center;"><i class="fa-solid fa-sliders"></i> 맞춤 상황 입력</h2>
          <p style="color: var(--text-light); margin-bottom: 20px; text-align: center;">원하시는 조건만 선택해주세요. 나머지는 AI가 알아서 판단합니다.</p>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: left;">
          <div>
            <label style="font-weight: bold; font-size: 0.9rem;">MBTI</label>
            <div class="mbti-picker">
              <select v-model="recommendModal.params.mbti_ei" class="input-field">
                <option value="">-</option>
                <option value="E">E</option>
                <option value="I">I</option>
              </select>
              <select v-model="recommendModal.params.mbti_sn" class="input-field">
                <option value="">-</option>
                <option value="S">S</option>
                <option value="N">N</option>
              </select>
              <select v-model="recommendModal.params.mbti_tf" class="input-field">
                <option value="">-</option>
                <option value="T">T</option>
                <option value="F">F</option>
              </select>
              <select v-model="recommendModal.params.mbti_jp" class="input-field">
                <option value="">-</option>
                <option value="J">J</option>
                <option value="P">P</option>
              </select>
            </div>
          </div>
          <div>
            <label style="font-weight: bold; font-size: 0.9rem;">인원수</label>
            <select v-model="recommendModal.params.players" class="input-field" style="margin-bottom: 0;">
              <option value="">상관없음</option>
              <option value="2인">2인 (커플/친구)</option>
              <option value="3~4인">3~4인</option>
              <option value="5인 이상">5인 이상 (다인원)</option>
            </select>
          </div>
          <div>
            <label style="font-weight: bold; font-size: 0.9rem;">플레이 시간</label>
            <select v-model="recommendModal.params.time" class="input-field" style="margin-bottom: 0;">
              <option value="">상관없음</option>
              <option value="30분 이하">30분 이하 (가볍게)</option>
              <option value="1시간 내외">1시간 내외</option>
              <option value="2시간 이상">2시간 이상 (각잡고)</option>
            </select>
          </div>
          <div>
            <label style="font-weight: bold; font-size: 0.9rem;">난이도</label>
            <select v-model="recommendModal.params.difficulty" class="input-field" style="margin-bottom: 0;">
              <option value="">상관없음</option>
              <option value="쉬움">쉬움 (초보자 환영)</option>
              <option value="보통">보통 (어느정도 해봄)</option>
              <option value="어려움">어려움 (보드게임 긱)</option>
            </select>
          </div>
          <div>
            <label style="font-weight: bold; font-size: 0.9rem;">성향</label>
            <select v-model="recommendModal.params.preference" class="input-field" style="margin-bottom: 0;">
              <option value="">상관없음</option>
              <option value="파티게임">파티/시끌벅적</option>
              <option value="전략게임">전략/두뇌싸움</option>
              <option value="협력게임">협력/원팀</option>
              <option value="마피아">마피아/블러핑</option>
            </select>
          </div>
          <div>
            <label style="font-weight: bold; font-size: 0.9rem;">테마</label>
            <input v-model="recommendModal.params.theme" class="input-field" placeholder="예: 좀비, 판타지, 방탈출..." style="margin-bottom: 0;" @keyup.enter="submitRecommend" />
          </div>
        </div>

        <div style="margin-top: 15px; text-align: left;">
          <label style="font-weight: bold; font-size: 0.9rem;">AI에게 한마디</label>
          <textarea
            v-model="recommendModal.params.ai_comment"
            class="input-field"
            placeholder="예: 룰 설명 싫어하는 친구가 있어요. 말 많이 하고 웃긴 게임이면 좋겠어요."
            rows="3"
            style="margin-bottom: 0; resize: vertical;"
          ></textarea>
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
          <button class="btn btn-brown" @click="submitRecommend" :disabled="aiLoading" style="width: 100%; padding: 1rem; font-size: 1.1rem;">
            <i class="fa-solid" :class="aiLoading ? 'fa-spinner fa-spin' : 'fa-wand-magic-sparkles'"></i> 
            {{ aiLoading ? 'AI가 고민 중...' : '이 조건으로 추천받기' }}
          </button>
        </div>
        <p v-if="aiError" style="color: red; margin-top: 10px;">{{ aiError }}</p>
      </template>
      
      <!-- Step 2: Results -->
      <template v-else-if="recommendModal.step === 2">
        <div style="display: flex; flex-direction: column; gap: 15px;">
            <div class="recommend-result-actions">
              <div>
                <strong>추천 결과</strong>
                <p>게임을 눌러 상세 정보를 확인하고 리뷰를 남기면, 나중에 프로필에서 다시 볼 수 있어요.</p>
              </div>
              <button class="btn btn-outline result-refresh-btn" type="button" @click="refreshRecommendations" :disabled="aiLoading">
                <i class="fa-solid fa-rotate"></i> 새로 추천
              </button>
            </div>

            <div v-if="aiLoading" class="card" style="margin: 0; text-align: center; padding: 2rem;">
              <i class="fa-solid fa-spinner fa-spin" style="color: var(--primary-color); font-size: 1.5rem;"></i>
              <p style="margin: 0.8rem 0 0; color: var(--text-light);">조건에 맞는 게임을 새로 고르는 중...</p>
            </div>

            <template v-else>
              <div v-for="item in aiRecommendations" :key="item.game_id || item.title" class="card ai-item" @click="openAiRecommendModal(item.title, { displayTitle: displayGameTitle(item) })" style="margin: 0;">
                <div class="ai-item-content" style="display: flex; gap: 15px; align-items: flex-start;">
                  <img v-if="item.image_url" :src="item.image_url" alt="board game cover" class="ai-item-image" />
                  <div class="ai-item-text" style="text-align: left;">
                    <strong style="color: var(--primary-color); text-decoration: underline; font-size: 1.1rem;">{{ displayGameTitle(item) }}</strong><br />
                    <span style="font-size: 0.95rem; color: var(--text-dark); display: inline-block; margin-top: 5px;">{{ item.reason }}</span>
                  </div>
                </div>
              </div>
            </template>
            <p v-if="aiError" style="color: red; text-align: center;">오류: {{ aiError }}</p>
        </div>
        </template>
      </div>
    </div>
  </div>

  <!-- Ranking Modal -->
  <div v-if="rankingModalOpen" class="modal-overlay" @click.self="closeRankingModal">
    <div class="modal-content retro-window" style="padding: 3px; width: 500px;">
      <div class="retro-titlebar">
        <span><i class="fa-solid fa-trophy"></i> 전체_보드게임_순위.exe</span>
        <div class="retro-titlebar-close" @click="closeRankingModal">X</div>
      </div>
      <div class="retro-content-inner" style="padding: 20px;">
        <h2 style="text-align: center; margin-bottom: 15px; color: var(--primary-color);">🏆 명예의 전당</h2>
        <input type="text" v-model="rankingSearchQuery" class="input-field" placeholder="게임명 검색..." style="margin-bottom: 15px; width: 100%; border: 2px solid var(--primary-color);" />
        
        <div style="max-height: 400px; overflow-y: auto; border: 2px solid #ccc; background: #fff;">
          <table class="games-table" style="width: 100%; margin: 0; border-collapse: collapse;">
            <thead style="background: #eadecc; position: sticky; top: 0;">
              <tr>
                <th style="padding: 8px; text-align: center; border-bottom: 2px solid var(--primary-color);">순위</th>
                <th style="padding: 8px; text-align: left; border-bottom: 2px solid var(--primary-color);">게임명</th>
                <th style="padding: 8px; text-align: right; border-bottom: 2px solid var(--primary-color);">조회수</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="game in filteredRankings" :key="game.game_id" @click="openGameModal(game.game_id, game.title)" style="cursor: pointer; border-bottom: 1px solid #eee;">
                <td style="padding: 10px; text-align: center; font-weight: bold;" :style="{ color: game.rank <= 3 ? 'red' : 'var(--text-light)' }">{{ game.rank }}</td>
                <td style="padding: 10px; font-weight: bold;">{{ game.title }}</td>
                <td style="padding: 10px; text-align: right; color: var(--text-light); font-size: 0.85rem;"><i class="fa-regular fa-eye"></i> {{ game.view_count || 0 }}</td>
              </tr>
              <tr v-if="filteredRankings.length === 0">
                <td colspan="3" style="text-align: center; padding: 20px; color: var(--text-light);">검색 결과가 없습니다.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

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


  <div v-if="gameModal.open" class="modal-overlay" @click.self="closeGameDetail">
    <div class="modal-content wide retro-window" style="padding: 3px;">
      <div class="retro-titlebar">
        <span id="retroModalTitle">
          <i class="fa-solid fa-gamepad"></i> {{ gameModal.title }}.exe
        </span>
        <div class="retro-titlebar-close" @click="closeGameDetail">X</div>
      </div>
      <div class="retro-content-inner" style="background:var(--bg-color); padding:1.5rem; text-align:center;">
        <div v-if="gameModal.loading" style="margin: 2rem 0;"><i class="fa-solid fa-spinner fa-spin"></i> 게임 정보를 불러오는 중...</div>
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
            <div class="modal-review-toggle-row">
              <button class="btn btn-outline modal-review-toggle" type="button" @click="openModalReview">
                <i class="fa-regular fa-pen-to-square"></i>
                리뷰
              </button>
            </div>
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
  </div>

  <div v-if="gameModal.reviewOpen && feedbackForms[modalFeedbackTitle]" class="modal-overlay review-overlay" @click.self="closeModalReview">
    <div class="modal-content review-modal">
      <button class="modal-close" type="button" @click="closeModalReview">&times;</button>
      <div class="modal-feedback-box">
        <h4>{{ modalFeedbackTitle }} 리뷰</h4>
        <p>별점, 함께한 인원, 짧은 리뷰를 남기면 프로필에서 다시 볼 수 있고 다음 추천에도 반영할 수 있어요.</p>
        <div class="feedback-form">
          <div class="feedback-grid">
            <label>
              별점
              <select v-model="feedbackForms[modalFeedbackTitle].rating" class="input-field">
                <option value="">선택 안 함</option>
                <option value="5">5점</option>
                <option value="4">4점</option>
                <option value="3">3점</option>
                <option value="2">2점</option>
                <option value="1">1점</option>
              </select>
            </label>
            <label>
              인원
              <input v-model="feedbackForms[modalFeedbackTitle].player_count" class="input-field" type="number" min="1" placeholder="예: 4" />
            </label>
          </div>
          <textarea v-model="feedbackForms[modalFeedbackTitle].review" class="input-field" placeholder="이 게임 어땠나요? 짧게 남겨보세요." rows="4"></textarea>
          <div class="feedback-form-actions">
            <span class="feedback-status">{{ feedbackForms[modalFeedbackTitle].status }}</span>
            <button class="btn btn-brown feedback-save-btn" type="button" @click="saveRecommendationFeedback({ title: modalFeedbackTitle, reason: gameModal.summary })" :disabled="feedbackForms[modalFeedbackTitle].saving">
              <i class="fa-solid fa-floppy-disk"></i>
              {{ feedbackForms[modalFeedbackTitle].saving ? '저장 중...' : '리뷰 저장' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import BoardBackground from './components/BoardBackground.vue'
import TitleAnimation from './components/TitleAnimation.vue'

const view = ref('main')
const trendingGames = ref([])
const trendingLoading = ref(false)

const top5Games = computed(() => {
  return trendingGames.value.slice(0, 5).map((game, i) => ({ ...game, rank: i + 1 }))
})

const rankingModalOpen = ref(false)
const rankingSearchQuery = ref('')

const filteredRankings = computed(() => {
  const list = trendingGames.value.map((game, i) => ({ ...game, rank: i + 1 }))
  if (!rankingSearchQuery.value) return list
  return list.filter(game => game.title.toLowerCase().includes(rankingSearchQuery.value.toLowerCase()))
})

function openRankingModal() {
  rankingModalOpen.value = true
  rankingSearchQuery.value = ''
}
function closeRankingModal() {
  rankingModalOpen.value = false
}

const recommendModal = reactive({
  step: 0,
  params: {
    mbti_ei: '',
    mbti_sn: '',
    mbti_tf: '',
    mbti_jp: '',
    players: '',
    time: '',
    difficulty: '',
    preference: '',
    theme: '',
    ai_comment: '',
  }
})
const selectedMbti = computed(() => {
  const letters = [
    recommendModal.params.mbti_ei,
    recommendModal.params.mbti_sn,
    recommendModal.params.mbti_tf,
    recommendModal.params.mbti_jp,
  ]
  return letters.every(Boolean) ? letters.join('') : ''
})
const recommendationSituation = computed(() => {
  const labels = [
    ['MBTI', selectedMbti.value],
    ['인원수', recommendModal.params.players],
    ['시간', recommendModal.params.time],
    ['난이도', recommendModal.params.difficulty],
    ['성향', recommendModal.params.preference],
    ['테마', recommendModal.params.theme],
    ['추가 요청', recommendModal.params.ai_comment],
  ]
  const activeLabels = labels
    .filter(([, value]) => String(value || '').trim())
    .map(([label, value]) => `${label}: ${value}`)

  return activeLabels.length ? activeLabels.join(', ') : '상관없음'
})

const aiLoading = ref(false)
const aiError = ref('')
const aiRecommendations = ref([])
const recentViewedGames = ref([])
const currentRecentIndex = ref(0)
const currentRecentGame = computed(() => recentViewedGames.value[currentRecentIndex.value] || null)

function nextRecentGame() {
  if (recentViewedGames.value.length <= 1) return
  currentRecentIndex.value = (currentRecentIndex.value + 1) % recentViewedGames.value.length
}
function prevRecentGame() {
  if (recentViewedGames.value.length <= 1) return
  currentRecentIndex.value = (currentRecentIndex.value - 1 + recentViewedGames.value.length) % recentViewedGames.value.length
}
function addRecentViewedGame(title) {
  if (!title) return
  const existingIndex = recentViewedGames.value.findIndex(g => g.title === title)
  let imageUrl = ''
  if (existingIndex !== -1) {
    imageUrl = recentViewedGames.value[existingIndex].imageUrl || ''
    recentViewedGames.value.splice(existingIndex, 1)
  }
  recentViewedGames.value.unshift({ id: Date.now(), title, imageUrl })
  if (recentViewedGames.value.length > 20) recentViewedGames.value.pop()
  localStorage.setItem('recent_viewed_games', JSON.stringify(recentViewedGames.value))
  currentRecentIndex.value = 0
}
function updateRecentViewedGameImage(title, imageUrl) {
  if (!imageUrl) return
  const index = recentViewedGames.value.findIndex(g => g.title === title)
  if (index !== -1 && !recentViewedGames.value[index].imageUrl) {
    recentViewedGames.value[index].imageUrl = imageUrl
    localStorage.setItem('recent_viewed_games', JSON.stringify(recentViewedGames.value))
  }
}
function deleteCurrentRecentGame() {
  if (recentViewedGames.value.length === 0) return
  recentViewedGames.value.splice(currentRecentIndex.value, 1)
  localStorage.setItem('recent_viewed_games', JSON.stringify(recentViewedGames.value))
  if (currentRecentIndex.value >= recentViewedGames.value.length) {
    currentRecentIndex.value = Math.max(0, recentViewedGames.value.length - 1)
  }
}

const feedbackForms = reactive({})
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
  shareLoading: false,
  reviewOpen: false
})
const modalFeedbackTitle = computed(() => gameModal.title.replace(' (AI 추천)', '').trim())
const RECENT_RECOMMENDATIONS_KEY = 'boardgame_recent_recommendations'
const GAME_GUIDE_CACHE_KEY = 'boardgame_guide_cache'

function displayGameTitle(item) {
  return item?.display_title || item?.korean_title || item?.title || ''
}

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
  loadRecentViewedGames()
  fetchCurrentUser()
  fetchTrendingGames()
  openInitialToolFromUrl()
  startTicker()
})

onUnmounted(() => {
  if (tickerInterval) clearInterval(tickerInterval)
})

function showMain() {
  view.value = 'main'
}

function openRecommendInputModal() {
  recommendModal.step = 1
  aiError.value = ''
}

function closeRecommendModal() {
  recommendModal.step = 0
}

function backToRecommendInput() {
  recommendModal.step = 1
}

async function fetchTrendingGames() {
  trendingLoading.value = true
  try {
    const response = await fetch('/boardgames/api/trending/')
    const data = await response.json()
    trendingGames.value = data.games || []
  } catch (error) {
    console.error("Trending fetch error", error)
  } finally {
    trendingLoading.value = false
  }
}

async function submitRecommend(options = {}) {
  const excludeCurrent = options && options.excludeCurrent === true
  const excludeGameIds = excludeCurrent
    ? aiRecommendations.value.map((item) => item.game_id).filter(Boolean)
    : []

  aiLoading.value = true
  aiError.value = ''
  aiRecommendations.value = []
  resetFeedbackForms()
  recommendModal.step = 2

  try {
    const { mbti_ei, mbti_sn, mbti_tf, mbti_jp, ...recommendParams } = recommendModal.params
    const requestBody = {
      ...recommendParams,
      mbti: selectedMbti.value,
      exclude_game_ids: excludeGameIds,
    }

    const response = await fetch('/boardgames/recommend/', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify(requestBody)
    })
    const data = await response.json()
    if (data.error) {
      aiError.value = data.error
      return
    }
    aiRecommendations.value = data.recommendations || []
    aiRecommendations.value.forEach((item) => ensureFeedbackForm(item.title))
    recommendModal.step = 2
  } catch (error) {
    aiError.value = error.message
  } finally {
    aiLoading.value = false
  }
}


function refreshRecommendations() {
  submitRecommend({ excludeCurrent: true })
}

function loadRecentRecommendations() {

  try {
    recentViewedGames.value = JSON.parse(localStorage.getItem('recent_viewed_games') || '[]')
  } catch {
    recentViewedGames.value = []
  }
}

function getGuideCache() {
  try {
    return JSON.parse(localStorage.getItem(GAME_GUIDE_CACHE_KEY) || '{}')
  } catch {
    return {}
  }
}

function setGuideCache(key, value) {
  const cache = getGuideCache()
  cache[key] = {
    ...value,
    cachedAt: new Date().toISOString()
  }
  localStorage.setItem(GAME_GUIDE_CACHE_KEY, JSON.stringify(cache))
}

function getCachedGuide(key) {
  return getGuideCache()[key] || null
}

function guideTitleKey(title) {
  return `title:${title.trim().toLowerCase()}`
}

function guideIdKey(gameId) {
  return `id:${gameId}`
}

function createFeedbackForm() {
  return {
    open: false,
    rating: '',
    player_count: '',
    review: '',
    saving: false,
    status: ''
  }
}

function ensureFeedbackForm(title) {
  if (!feedbackForms[title]) {
    feedbackForms[title] = createFeedbackForm()
  }
  return feedbackForms[title]
}

function resetFeedbackForms() {
  Object.keys(feedbackForms).forEach((title) => {
    delete feedbackForms[title]
  })
}

async function saveRecommendationFeedback(item) {
  const form = ensureFeedbackForm(item.title)
  form.saving = true
  form.status = ''

  try {
    const response = await fetch('/boardgames/api/recommendation-feedback/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        game_title: item.title,
        situation: recommendationSituation.value,
        recommendation_reason: item.reason || '',
        rating: form.rating,
        player_count: form.player_count,
        review: form.review
      })
    })

    const data = await response.json()
    if (response.status === 401) {
      form.status = '로그인 후 저장할 수 있어요.'
      return
    }
    if (!response.ok || data.status !== 'success') {
      form.status = data.message || '저장에 실패했습니다.'
      return
    }

    form.status = '저장됐어요. 프로필에서 다시 볼 수 있습니다.'
    form.review = ''
  } catch (error) {
    form.status = `오류: ${error.message}`
  } finally {
    form.saving = false
  }
}

function openModalReview() {
  ensureFeedbackForm(modalFeedbackTitle.value)
  gameModal.reviewOpen = true
}

function closeModalReview() {
  gameModal.reviewOpen = false
}

async function openReviewFromRecent(title, displayTitle = '') {
  await openAiRecommendModal(title, { openReview: true, displayTitle })
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
  addRecentViewedGame(title)
  gameModal.loading = true

  try {
    const response = await fetch(`/boardgames/api/${gameId}/details/`)
    if (!response.ok) throw new Error('Details not found')
    gameModal.details = await response.json()
    if (gameModal.details) {
      updateRecentViewedGameImage(title, gameModal.details.image || gameModal.details.thumbnail || '')
    }
    gameModal.loading = false
    fetchGameSmartGuide(gameId)
  } catch {
    gameModal.loading = false
    gameModal.summary = '상세 정보가 데이터베이스에 없습니다.'
  }
}

async function fetchGameSmartGuide(gameId) {
  const cacheKey = guideIdKey(gameId)
  const cached = getCachedGuide(cacheKey)
  if (cached) {
    gameModal.summary = cached.summary || ''
    gameModal.youtubeVideoId = cached.youtubeVideoId || ''
    gameModal.guideLoading = false
    return
  }

  gameModal.guideLoading = true
  try {
    const response = await fetch(`/boardgames/${gameId}/recommend/`)
    const data = await response.json()
    gameModal.summary = data.summary || ''
    gameModal.youtubeVideoId = data.youtube_videoId || ''
    setGuideCache(cacheKey, {
      summary: gameModal.summary,
      youtubeVideoId: gameModal.youtubeVideoId
    })
  } finally {
    gameModal.guideLoading = false
  }
}

async function openAiRecommendModal(title, options = {}) {

  const modalTitle = options.displayTitle || title
  resetGameModal(`${modalTitle} (AI 추천)`)
  
  addRecentViewedGame(title)

  gameModal.loading = true
  gameModal.guideLoading = true

  try {
    const cacheKey = guideTitleKey(title)
    const cached = getCachedGuide(cacheKey)
    if (cached) {
      gameModal.details = cached.details || null
      gameModal.summary = cached.summary || ''
      gameModal.youtubeVideoId = cached.youtubeVideoId || ''
      return
    }

    const response = await fetch(`/boardgames/api/details_by_title/?title=${encodeURIComponent(title)}`)
    const data = await response.json()
    gameModal.details = data.details || null
    gameModal.summary = data.ai_summary || ''
    gameModal.youtubeVideoId = data.youtube_videoId || ''
    if (gameModal.details) {
      updateRecentViewedGameImage(title, gameModal.details.image || gameModal.details.thumbnail || '')
    }
    setGuideCache(cacheKey, {
      details: gameModal.details,
      summary: gameModal.summary,
      youtubeVideoId: gameModal.youtubeVideoId
    })
  } finally {
    gameModal.loading = false
    gameModal.guideLoading = false
    if (options.openReview) {
      gameModal.reviewOpen = true
    }
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
      gameModal.shareContent = `#${cleanTitle} `;
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
  gameModal.shareContent = `#${modalFeedbackTitle.value} `
  gameModal.shareLoading = false
  gameModal.reviewOpen = false
  ensureFeedbackForm(modalFeedbackTitle.value)
}
</script>
