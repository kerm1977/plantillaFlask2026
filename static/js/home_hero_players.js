// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
(function() {
  'use strict';
  const H = window._hero;
  if (!H) return;
  function setupControls() {
    H.playPauseBtn.addEventListener('click', function() {
      H.isPlaying = !H.isPlaying;
      H.updatePlayPauseIcon();
      if (H.isPlaying) {
        const type = H.slides[H.current].dataset.type;
        if (type !== 'video') H.startAutoplay();
        H.playSlideMedia(H.current);
      } else {
        H.stopAutoplay();
        H.pauseSlideMedia(H.current);
      }
    });

    H.muteBtn.addEventListener('click', function() {
      H.isMuted = !H.isMuted;
      H.updateMuteIcon();
      const type = H.slides[H.current].dataset.type;
      if (type === 'youtube') {
        const player = H.ytPlayers[H.slides[H.current].firstElementChild.id];
        if (player) {
          if (H.isMuted) player.mute(); else player.unMute();
        }
      } else if (type === 'facebook') {
        const fb = window._fbPlayers && window._fbPlayers[H.current];
        if (fb) {
          if (H.isMuted) fb.mute(); else fb.unmute();
        }
      } else if (type === 'video') {
        const v = H.getLocalVideo(H.slides[H.current]);
        if (v) v.muted = H.isMuted;
      }
    });

    H.volumeInput.addEventListener('input', function() {
      H.volume = parseInt(this.value, 10);
      const type = H.slides[H.current].dataset.type;
      if (type === 'youtube') {
        const player = H.ytPlayers[H.slides[H.current].firstElementChild.id];
        if (player && player.setVolume) player.setVolume(H.volume);
      } else if (type === 'facebook') {
        const fb = window._fbPlayers && window._fbPlayers[H.current];
        if (fb && fb.setVolume) {
          try { fb.setVolume(H.volume / 100); } catch (e) {}
        }
      } else if (type === 'video') {
        const v = H.getLocalVideo(H.slides[H.current]);
        if (v) v.volume = H.volume / 100;
      }
    });
  }

  function initYouTubePlayers() {
    H.slides.forEach(function(slide) {
      if (slide.dataset.type !== 'youtube') return;
      const container = slide.firstElementChild;
      const rawUrl = container.dataset.ytUrl || '';
      const videoId = extractYouTubeId(rawUrl);
      if (!videoId) return;
      const playerId = container.id;
      H.ytPlayers[playerId] = new YT.Player(playerId, {
        width: '100%',
        height: '100%',
        videoId: videoId,
        playerVars: {
          autoplay: 0,
          controls: 0,
          disablekb: 1,
          fs: 0,
          rel: 0,
          modestbranding: 1,
          playsinline: 1
        },
        events: {
          onReady: function() {}
        }
      });
    });
  }

  function extractYouTubeId(url) {
    if (!url) return '';
    const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : '';
  }

  window.onYouTubeIframeAPIReady = function() {
    H.ytReady = true;
    initYouTubePlayers();
    H.playSlideMedia(H.current);
  };

  window.initHomeCarousel = function() {
    if (H.carouselInitialized) return;
    H.carouselInitialized = true;
    H.loadCarouselState();
    H.slides.forEach(function(slide) {
      const v = H.getLocalVideo(slide);
      if (v) v.addEventListener('ended', H.nextSlide);
    });
    setupControls();
    H.updatePlayPauseIcon();
    H.updateMuteIcon();
    if (H.volumeInput) H.volumeInput.value = H.volume;
    H.showSlide(H.current, true);
    window.addEventListener('beforeunload', H.saveCarouselState);
    document.addEventListener('visibilitychange', H.handleVisibility);
  };

  // Inicializar controles inmediatamente; los reproductores se activan cuando cada API esté lista.
  window.initHomeCarousel();

  // Si Facebook ya está listo, inicializar reproductores FB.
  if (window.FB && window.FB.Event) {
    window.initHomeCarousel();
  }
})();

