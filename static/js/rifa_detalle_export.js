// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// ==========================================
// FUNCIONES DE EXPORTACIÓN DE RIFA DETALLE
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Attach event listeners to export links
    const exportLinks = document.querySelectorAll('.export-link');
    exportLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const format = this.getAttribute('data-format');
            exportRifa(format);
        });
    });
});

async function exportRifa(format) {
    const maxRetries = 3;
    let retryCount = 0;
    
    while (retryCount < maxRetries) {
        try {
            // Get raffle ID from URL
            const pathParts = window.location.pathname.split('/');
            const raffleId = pathParts[pathParts.length - 1];
            
            // Fetch data from API
            const response = await fetch(`/api/rifas/${raffleId}/export-data`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const config = await response.json();
            
            switch(format) {
                case 'whatsapp':
                    exportToWhatsApp(config);
                    break;
                case 'txt':
                    exportToTXT(config);
                    break;
                case 'pdf':
                    exportToPDF(config);
                    break;
                default:
                    alert('Formato no soportado');
            }
            return; // Success, exit function
        } catch (error) {
            retryCount++;
            console.error(`Intento ${retryCount}/${maxRetries} falló:`, error);
            
            if (retryCount >= maxRetries) {
                alert('Error: No se pudieron obtener los datos de la rifa después de varios intentos. Por favor recarga la página.');
                return;
            }
            
            // Wait before retrying (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
        }
    }
}

function exportToWhatsApp(config) {
    let text = `🎟️ *RIFA: ${config.name}* (#${config.raffle_number})\n\n`;
    text += `📋 *Detalle:* ${config.detail}\n`;
    text += `💰 *Precio:* ₡${config.price}\n`;
    text += `🏆 *Premio:* ${config.prize}\n`;
    text += `📅 *Fecha:* ${config.raffle_date}\n`;
    if (config.raffle_time) {
        text += `⏰ *Hora:* ${config.raffle_time}\n`;
    }
    if (config.sinpe_name && config.sinpe_phone) {
        text += `\n💳 *SINPE:*\n${config.sinpe_name}\n${config.sinpe_phone}\n`;
    }
    text += `\n📊 *Total vendidos:* ${config.total_sold}/100\n\n`;
    
    if (config.selections && Object.keys(config.selections).length > 0) {
        text += `📝 *SELECCIONES:*\n\n`;
        let totalPending = 0;
        
        Object.entries(config.selections).forEach(([phone, data]) => {
            text += `👤 *${data.name}*\n`;
            text += `📱 ${phone}\n`;
            text += `🔢 Números: ${data.numbers.join(', ')}\n`;
            text += `💵 Total: ₡${data.total}\n`;
            if (data.is_paid) {
                text += `✅ PAGADO\n`;
            } else {
                text += `⏳ PENDIENTE\n`;
                totalPending += data.total;
            }
            text += `\n`;
        });
        
        if (totalPending > 0) {
            text += `💰 *Total pendiente de cobro:* ₡${totalPending}\n`;
        }
    } else {
        text += `📝 No hay selecciones registradas\n`;
    }

    const encodedText = encodeURIComponent(text);
    const whatsappUrl = `https://wa.me/?text=${encodedText}`;
    window.open(whatsappUrl, '_blank');
}

function exportToTXT(config) {
    let text = `RIFA: ${config.name} (#${config.raffle_number})\n`;
    text += `${'='.repeat(50)}\n\n`;
    text += `Detalle: ${config.detail}\n`;
    text += `Precio: ₡${config.price}\n`;
    text += `Premio: ${config.prize}\n`;
    text += `Fecha: ${config.raffle_date}\n`;
    if (config.raffle_time) {
        text += `Hora: ${config.raffle_time}\n`;
    }
    if (config.sinpe_name && config.sinpe_phone) {
        text += `\nSINPE:\n${config.sinpe_name}\n${config.sinpe_phone}\n`;
    }
    text += `\nTotal vendidos: ${config.total_sold}/100\n\n`;
    
    if (config.selections && Object.keys(config.selections).length > 0) {
        text += `SELECCIONES:\n${'='.repeat(50)}\n\n`;
        let totalPending = 0;
        
        Object.entries(config.selections).forEach(([phone, data]) => {
            text += `Nombre: ${data.name}\n`;
            text += `Teléfono: ${phone}\n`;
            text += `Números: ${data.numbers.join(', ')}\n`;
            text += `Total: ₡${data.total}\n`;
            text += `Estado: ${data.is_paid ? 'PAGADO' : 'PENDIENTE'}\n`;
            if (!data.is_paid) {
                totalPending += data.total;
            }
            text += `\n`;
        });
        
        if (totalPending > 0) {
            text += `Total pendiente de cobro: ₡${totalPending}\n`;
        }
    } else {
        text += `No hay selecciones registradas\n`;
    }

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rifa_${config.name.replace(/\s+/g, '_')}_${config.raffle_number}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
