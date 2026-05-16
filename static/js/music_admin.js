// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ INICIO DE CORTE: music_admin.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️

// ==========================================
// EDITOR VISUAL Y GESTIÓN DE MÚSICA
// ==========================================

async function quickUploadCover(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('logo', file);

    try {
        const bigCover = document.getElementById('bigCover');
        if(bigCover) bigCover.style.opacity = '0.5';
        
        const res = await fetch('/api/upload_default_logo', { method: 'POST', body: formData });
        
        if(!res.ok) {
            const err = await res.json();
            throw new Error(err.error || "Error del servidor al subir la imagen");
        }
        
        const newLogoUrl = `/static/music/logo.png?t=${new Date().getTime()}`;
        
        if(bigCover) bigCover.src = newLogoUrl;
        const miniCover = document.getElementById('miniCover');
        if(miniCover) miniCover.src = newLogoUrl;
        
        document.querySelectorAll('.playlist-item img').forEach(img => {
            img.src = newLogoUrl;
        });

        const adminPreview = document.getElementById('musicCoverPreviewImg');
        if(adminPreview) adminPreview.src = newLogoUrl;
        
        alert("¡Logo global actualizado! Esta imagen será la portada fija para todas las canciones.");
        
    } catch (err) {
        alert("Atención: " + err.message);
    } finally {
        const bigCover = document.getElementById('bigCover');
        if(bigCover) bigCover.style.opacity = '1';
        event.target.value = '';
    }
}

const mCoverUpload = document.getElementById('musicCoverUpload');
const mCoverPreview = document.getElementById('musicCoverPreviewImg');
const mScale = document.getElementById('musicScaleSlider');
const mPosX = document.getElementById('musicPosXSlider');
const mPosY = document.getElementById('musicPosYSlider');

if(mScale && mPosX && mPosY) {
    function updateMusicTransform() {
        mCoverPreview.style.transform = `scale(${mScale.value}) translate(${mPosX.value}px, ${mPosY.value}px)`;
    }
    mScale.addEventListener('input', updateMusicTransform);
    mPosX.addEventListener('input', updateMusicTransform);
    mPosY.addEventListener('input', updateMusicTransform);

    if(mCoverUpload) {
        mCoverUpload.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    mCoverPreview.src = evt.target.result;
                    mScale.value = 1; mPosX.value = 0; mPosY.value = 0; updateMusicTransform();
                }
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }
}

async function getCroppedMusicCoverBlob() {
    if (!mCoverPreview || !mCoverPreview.src) return null;
    if (mCoverPreview.src.includes('logo.png') || mCoverPreview.src.includes('base64')) return null;

    const canvas = document.createElement('canvas');
    const size = 400; 
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    const scale = parseFloat(mScale.value);
    const posX = parseFloat(mPosX.value);
    const posY = parseFloat(mPosY.value);

    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, size, size);

    const imgRatio = mCoverPreview.naturalWidth / mCoverPreview.naturalHeight;
    let drawW = size;
    let drawH = size;
    if (imgRatio > 1) { drawW = size * imgRatio; } 
    else { drawH = size / imgRatio; }

    ctx.save();
    ctx.translate(size/2, size/2);
    ctx.scale(scale, scale);
    ctx.translate(posX, posY);
    ctx.drawImage(mCoverPreview, -drawW/2, -drawH/2, drawW, drawH);
    ctx.restore();

    return new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9));
}

async function applyCoverToSpecificSong(id) {
    const blob = await getCroppedMusicCoverBlob();
    if (!blob) { alert('Sube y ajusta una imagen en el editor de arriba primero.'); return; }

    const headerEl = document.querySelector('#musicAdminModal .modal-title');
    const originalHTML = headerEl.innerHTML;
    headerEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2 text-white"></span> Aplicando Portada...';

    try {
        const fd = new FormData();
        fd.append('cover', blob, `portada_${id}_${new Date().getTime()}.jpg`);
        const res = await fetch(`/api/songs/${id}`, { method: 'PUT', body: fd });
        
        if (res.ok) {
            await fetchAndRenderSongs(); 
            
            if (currentIdx !== -1 && songsList[currentIdx] && songsList[currentIdx].id === id) {
                const updatedSong = songsList[currentIdx];
                const safeCover = (updatedSong.cover === 'logo.png' || !updatedSong.cover) ? 'logo.png' : updatedSong.cover;
                const coverUrl = `/static/music/${safeCover}?v=${new Date().getTime()}`;
                const miniCover = document.getElementById('miniCover');
                const bigCover = document.getElementById('bigCover');
                if(miniCover) miniCover.src = coverUrl;
                if(bigCover) bigCover.src = coverUrl;
            }
            alert('Portada aplicada a la canción exitosamente.');
        } else {
            alert('Error al aplicar la portada.');
        }
    } catch (e) {
        alert('Error de conexión.');
    }
    headerEl.innerHTML = originalHTML;
}

async function uploadNewSongModal() {
    const audioInput = document.getElementById('musicAudioUpload');
    if (!audioInput.files || !audioInput.files[0]) {
        alert('Selecciona un archivo MP3 de tu dispositivo.'); return;
    }

    const formData = new FormData();
    formData.append('audio', audioInput.files[0]);
    
    let cleanTitle = audioInput.files[0].name.replace('.mp3', '').replace(/_/g, ' ');
    formData.append('title', cleanTitle);

    const blob = await getCroppedMusicCoverBlob();
    if (blob) formData.append('cover', blob, `portada_${new Date().getTime()}.jpg`);

    const headerEl = document.querySelector('#musicAdminModal .modal-title');
    const originalHTML = headerEl.innerHTML;
    headerEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2 text-white"></span> Procesando...';
    
    try {
        const response = await fetch('/api/songs', { method: 'POST', body: formData });
        if (response.ok) {
            alert('¡Canción y Portada subidas con éxito!');
            audioInput.value = '';
            await fetchAndRenderSongs();
        } else {
            alert("Ocurrió un error al guardar el archivo.");
        }
    } catch (err) { alert("Problema de red al subir la canción."); }
    
    headerEl.innerHTML = originalHTML;
}

async function applyGlobalCover() {
    if (songsList.length === 0) { alert('No hay canciones a las cuales aplicarles la portada.'); return; }
    
    const blob = await getCroppedMusicCoverBlob();
    if (!blob) { alert('Debes seleccionar una imagen desde tu galería primero.'); return; }

    if (!confirm('¿Aplicar esta misma imagen recortada a TODAS las canciones? Esta acción tomará unos segundos.')) return;

    const headerEl = document.querySelector('#musicAdminModal .modal-title');
    const originalHTML = headerEl.innerHTML;
    headerEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2 text-white"></span> Aplicando a Todas...';

    try {
        for (let song of songsList) {
            const fd = new FormData();
            fd.append('cover', blob, `portada_${song.id}_${new Date().getTime()}.jpg`);
            await fetch(`/api/songs/${song.id}`, { method: 'PUT', body: fd });
        }
        
        const logoFormData = new FormData();
        logoFormData.append('logo', blob, 'logo.jpg');
        await fetch('/api/upload_default_logo', { method: 'POST', body: logoFormData });

        alert('¡Carátula maestra aplicada a todas tus canciones y al reproductor global!');
        await fetchAndRenderSongs();
        
        const newLogoUrl = `/static/music/logo.png?t=${new Date().getTime()}`;
        const miniCover = document.getElementById('miniCover');
        const bigCover = document.getElementById('bigCover');
        if(miniCover) miniCover.src = newLogoUrl;
        if(bigCover) bigCover.src = newLogoUrl;
        
    } catch(e) { alert('Hubo problemas al aplicar a toda la lista.'); }
    
    headerEl.innerHTML = originalHTML;
}

async function editSong(id, currentTitle) {
    const newTitle = prompt("Escribe el nuevo título para esta canción:", currentTitle);
    if (!newTitle || newTitle === currentTitle) return;

    const formData = new FormData();
    formData.append('title', newTitle);
    
    try {
        const res = await fetch(`/api/songs/${id}`, { method: 'PUT', body: formData });
        if(res.ok) await fetchAndRenderSongs();
    } catch (err) { alert("Error de conexión al renombrar."); }
}

async function deleteSong(id) {
    if (!confirm("¿Estás seguro de que quieres borrar esta canción y su archivo permanentemente?")) return;
    
    try {
        const res = await fetch(`/api/songs/${id}`, { method: 'DELETE' });
        if(res.ok) {
            if(songsList[currentIdx] && songsList[currentIdx].id === id) {
                closeMiniPlayer(); 
            }
            await fetchAndRenderSongs();
        } else {
            alert("Error al intentar borrar en el servidor.");
        }
    } catch (err) { alert("Error de conexión al borrar."); }
}

// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ FIN DE CORTE: music_admin.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️

