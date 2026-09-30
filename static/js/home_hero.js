// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
(function() {
  'use strict';

  const carouselEl = document.getElementById('homeHeroCarousel');
  if (!carouselEl) return;
  const slides = document.querySelectorAll('.hero-slide');
  if (!slides.length) return;

  window._fbSlideIndices = Array.from(slides).map(function(s, i) { return s.dataset.type === 'facebook' ? i : null; }).filter(function(x) { return x !== null; });


  const playPauseBtn = document.getElementById('heroPlayPause');
  const muteBtn = document.getElementById('heroMute');
  const volumeInput = document.getElementById('heroVolume');

  const H = window._hero = {
    carouselEl, slides, playPauseBtn, muteBtn, volumeInput,
    current: 0, isPlaying: true, isMuted: false, volume: 50, resumeAt: null,
    interval: null, ytReady: false, carouselInitialized: false, ytPlayers: {},
    SLIDE_INTERVAL: 8000
  };

  function showSlide(idx, force) {
    if (idx === H.current && slides.length > 1 && !force) return;
    pauseSlideMedia(H.current);
    slides.forEach(function(s, i) {
      s.classList.toggle('active', i === idx);
    });
    H.current = idx;
    const type = slides[H.current].dataset.type;
    if (type === 'video') {
      stopAutoplay();
    } else {
      startAutoplay();
    }
    playSlideMedia(H.current);
  }

  function nextSlide() {
    showSlide((H.current + 1) % slides.length);
  }

  function getLocalVideo(slide) {
    return slide && slide.querySelector('video.hero-local-video');
  }

  function pauseSlideMedia(idx) {
    const slide = slides[idx];
    if (!slide) return;
    const type = slide.dataset.type;
    if (type === 'youtube') {
      const player = H.ytPlayers[slide.firstElementChild.id];
      if (player && player.pauseVideo) player.pauseVideo();
    } else if (type === 'facebook') {
      const fb = window._fbPlayers && window._fbPlayers[idx];
      if (fb && fb.pause) fb.pause();
    } else if (type === 'video') {
      const v = getLocalVideo(slide);
      if (v) v.pause();
    }
  }

  function playSlideMedia(idx) {
    if (!H.isPlaying) return;
    const slide = slides[idx];
    const type = slide.dataset.type;
    let usedResume = false;
    if (type === 'youtube') {
      const player = H.ytPlayers[slide.firstElementChild.id];
      if (player && player.playVideo) {
        if (H.isMuted) player.mute(); else player.unMute();
        player.setVolume(H.volume);
        if (H.resumeAt && player.seekTo) {
          player.seekTo(H.resumeAt, true);
          usedResume = true;
        }
        player.playVideo();
      }
    } else if (type === 'facebook') {
      const fb = window._fbPlayers && window._fbPlayers[idx];
      if (fb && fb.play) {
        if (H.isMuted) fb.mute(); else fb.unmute();
        try { fb.setVolume(H.volume / 100); } catch (e) {}
        fb.play();
      }
    } else if (type === 'video') {
      const v = getLocalVideo(slide);
      if (v) {
        v.muted = H.isMuted;
        v.volume = H.volume / 100;
        if (H.resumeAt) {
          v.currentTime = H.resumeAt;
          usedResume = true;
        }
        v.play().catch(function() {});
      }
    }
    if (usedResume) H.resumeAt = null;
  }

  function startAutoplay() {
    if (H.interval) clearInterval(H.interval);
    H.interval = setInterval(nextSlide, H.SLIDE_INTERVAL);
  }

  function stopAutoplay() {
    if (H.interval) clearInterval(H.interval);
    H.interval = null;
  }

  function updatePlayPauseIcon() {
    playPauseBtn.innerHTML = H.isPlaying
      ? '<i class="bi bi-pause-fill"></i>'
      : '<i class="bi bi-play-fill"></i>';
  }

  function updateMuteIcon() {
    muteBtn.innerHTML = H.isMuted
      ? '<i class="bi bi-volume-mute-fill"></i>'
      : '<i class="bi bi-volume-up-fill"></i>';
  }

  function getSlideResumeTime(idx) {
    const slide = slides[idx];
    if (!slide) return 0;
    const type = slide.dataset.type;
    if (type === 'video') {
      const v = getLocalVideo(slide);
      return v ? v.currentTime : 0;
    } else if (type === 'youtube') {
      const player = H.ytPlayers[slide.firstElementChild.id];
      return (player && player.getCurrentTime) ? player.getCurrentTime() : 0;
    }
    return 0;
  }

  function saveCarouselState() {
    try {
      const state = {
        current: H.current,
        isPlaying: H.isPlaying,
        isMuted: H.isMuted,
        volume: H.volume,
        resumeAt: getSlideResumeTime(H.current),
        slideType: slides[H.current] ? slides[H.current].dataset.type : '',
        savedAt: Date.now()
      };
      localStorage.setItem('homeCarouselState', JSON.stringify(state));
    } catch (e) {}
  }

  function loadCarouselState() {
    try {
      const raw = localStorage.getItem('homeCarouselState');
      if (!raw) return;
      const state = JSON.parse(raw);
      if (!state || typeof state.current !== 'number' || state.current < 0 || state.current >= slides.length) return;
      H.current = state.current;
      H.isPlaying = state.isPlaying !== false;
      H.isMuted = state.isMuted === true;
      H.volume = (typeof state.volume === 'number') ? state.volume : 50;
      H.resumeAt = (typeof state.resumeAt === 'number' && state.resumeAt > 0) ? state.resumeAt : null;
    } catch (e) {}
  }

  function handleVisibility() {
    if (document.hidden) {
      saveCarouselState();
      pauseSlideMedia(H.current);
    } else {
      if (H.isPlaying) playSlideMedia(H.current);
      const type = slides[H.current] ? slides[H.current].dataset.type : '';
      if (H.isPlaying && type !== 'video') startAutoplay();
    }
  }

  Object.assign(H, { showSlide, nextSlide, getLocalVideo, pauseSlideMedia,
    playSlideMedia, startAutoplay, stopAutoplay, updatePlayPauseIcon,
    updateMuteIcon, getSlideResumeTime, saveCarouselState, loadCarouselState,
    handleVisibility });
})();

