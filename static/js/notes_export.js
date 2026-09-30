// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Image Export (JPG/PNG/PDF)
function exportNoteJPG() {
    exportNoteImage('image/jpeg', 'jpg');
}

function exportNotePNG() {
    exportNoteImage('image/png', 'png');
}

function exportNotePDF() {
    exportNoteToPDF(
        document.getElementById('noteTitleInput').value || 'nota',
        document.getElementById('noteContentEditor').innerHTML
    );
}

function exportNoteImage(format, ext) {
    const title = document.getElementById('noteTitleInput').value || 'nota';
    const content = document.getElementById('noteContentEditor').innerHTML;
    
    // Crear canvas temporal
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 800;
    canvas.height = 600;
    
    // Fondo blanco
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Título
    ctx.fillStyle = '#000000';
    ctx.font = 'bold 24px Arial';
    ctx.fillText(title, 20, 40);
    
    // Contenido (simplificado - texto plano)
    ctx.font = '16px Arial';
    const plainText = stripHtml(content);
    const lines = wrapText(ctx, plainText, 760);
    let y = 80;
    lines.forEach(line => {
        if (y < canvas.height - 20) {
            ctx.fillText(line, 20, y);
            y += 24;
        }
    });
    
    // Descargar
    const url = canvas.toDataURL(format);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.${ext}`;
    a.click();
}

// WhatsApp Share
function shareNoteWhatsApp() {
    const title = document.getElementById('noteTitleInput').value || 'Nota';
    const content = htmlToWhatsApp(document.getElementById('noteContentEditor').innerHTML);
    const text = `*${title}*\n\n${content}`;
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
}

// View Modal Export Functions
function exportViewNoteJPG() {
    if (!currentViewNote) return;
    exportNoteImageFromData(currentViewNote.title, currentViewNote.content, 'image/jpeg', 'jpg');
}

function exportViewNotePNG() {
    if (!currentViewNote) return;
    exportNoteImageFromData(currentViewNote.title, currentViewNote.content, 'image/png', 'png');
}

function exportViewNotePDF() {
    if (!currentViewNote) return;
    exportNoteToPDF(currentViewNote.title, currentViewNote.content);
}

function exportViewNoteWhatsApp() {
    if (!currentViewNote) return;
    const text = `*${currentViewNote.title}*\n\n${htmlToWhatsApp(currentViewNote.content)}`;
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
}

async function exportNoteImageFromData(title, content, format, ext) {
    // Crear contenedor temporal fuera de la vista para renderizar con html2canvas
    const temp = document.createElement('div');
    temp.style.width = '800px';
    temp.style.padding = '30px';
    temp.style.background = '#ffffff';
    temp.style.color = '#000000';
    temp.style.fontFamily = 'Arial, sans-serif';
    temp.style.position = 'fixed';
    temp.style.left = '-9999px';
    temp.style.top = '0';
    temp.style.zIndex = '-1';
    temp.innerHTML = `
        <div style="text-align:center; margin-bottom:10px;">
            <h2 style="margin:0; font-size:28px; font-weight:bold;">${escapeHtml(title)}</h2>
            <hr style="border:0; border-top:2px solid #ff8c00; margin:10px 0;">
        </div>
        <div id="exportNoteContent" style="font-size:16px; line-height:1.6;">${content}</div>
    `;
    document.body.appendChild(temp);
    
    try {
        const canvas = await html2canvas(temp, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: 800
        });
        const url = canvas.toDataURL(format);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^a-z0-9\u00C0-\u024F\u1E00-\u1EFF]/gi, '_')}.${ext}`;
        a.click();
    } catch (e) {
        console.error('Error exportando imagen:', e);
        alert('Error al generar la imagen. Verifica que html2canvas esté cargado.');
    } finally {
        document.body.removeChild(temp);
    }
}

function exportNoteImage(format, ext) {
    const title = document.getElementById('noteTitleInput').value || 'nota';
    const content = document.getElementById('noteContentEditor').innerHTML;
    exportNoteImageFromData(title, content, format, ext);
}

async function exportNoteToPDF(title, content) {
    const temp = document.createElement('div');
    temp.style.width = '800px';
    temp.style.padding = '30px';
    temp.style.background = '#ffffff';
    temp.style.color = '#000000';
    temp.style.fontFamily = 'Arial, sans-serif';
    temp.style.position = 'fixed';
    temp.style.left = '-9999px';
    temp.style.top = '0';
    temp.style.zIndex = '-1';
    temp.innerHTML = `
        <div style="text-align:center; margin-bottom:10px;">
            <h2 style="margin:0; font-size:28px; font-weight:bold;">${escapeHtml(title)}</h2>
            <hr style="border:0; border-top:2px solid #ff8c00; margin:10px 0;">
        </div>
        <div style="font-size:16px; line-height:1.6;">${content}</div>
    `;
    document.body.appendChild(temp);
    
    try {
        const canvas = await html2canvas(temp, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: 800
        });
        const imgData = canvas.toDataURL('image/jpeg', 0.95);
        const response = await fetch('/api/notes/export-pdf', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title: title, image: imgData})
        });
        if (!response.ok) {
            const errJson = await response.json().catch(() => ({error: 'Error desconocido del servidor'}));
            console.error('Server PDF error:', errJson);
            throw new Error(errJson.error || 'Error del servidor');
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^a-z0-9\u00C0-\u024F\u1E00-\u1EFF]/gi, '_')}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Error exportando PDF:', e);
        alert('Error al generar el PDF.');
    } finally {
        document.body.removeChild(temp);
    }
}

