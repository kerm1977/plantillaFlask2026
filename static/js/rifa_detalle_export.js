// ==========================================
// FUNCIONES DE EXPORTACIÓN DE RIFA DETALLE
// ==========================================

function exportRifa(format) {
    const config = window.RIFA_CONFIG;
    if (!config) {
        console.error('RIFA_CONFIG no está definido');
        alert('Error: No hay datos de la rifa disponibles. Por favor recarga la página.');
        return;
    }

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

function exportToPDF(config) {
    // Generar contenido HTML para el PDF
    let htmlContent = `
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto;">
            <h1 style="color: #ff8c00; text-align: center;">RIFA: ${config.name} (#${config.raffle_number})</h1>
            <hr style="border-color: #ff8c00;">
            
            <div style="margin: 20px 0;">
                <p><strong>Detalle:</strong> ${config.detail}</p>
                <p><strong>Precio:</strong> ₡${config.price}</p>
                <p><strong>Premio:</strong> ${config.prize}</p>
                <p><strong>Fecha:</strong> ${config.raffle_date}</p>
    `;
    
    if (config.raffle_time) {
        htmlContent += `<p><strong>Hora:</strong> ${config.raffle_time}</p>`;
    }
    
    if (config.sinpe_name && config.sinpe_phone) {
        htmlContent += `
            <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #ff8c00; margin-top: 0;">SINPE</h3>
                <p><strong>${config.sinpe_name}</strong></p>
                <p><strong>${config.sinpe_phone}</strong></p>
            </div>
        `;
    }
    
    htmlContent += `
                <p><strong>Total vendidos:</strong> ${config.total_sold}/100</p>
            </div>
    `;
    
    if (config.selections && Object.keys(config.selections).length > 0) {
        htmlContent += `
            <h2 style="color: #ff8c00; margin-top: 30px;">SELECCIONES</h2>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background: #ff8c00; color: white;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Nombre</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Teléfono</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Números</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Total</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Estado</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        let totalPending = 0;
        
        Object.entries(config.selections).forEach(([phone, data]) => {
            htmlContent += `
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">${data.name}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${phone}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${data.numbers.join(', ')}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">₡${data.total}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: ${data.is_paid ? 'green' : 'red'}; font-weight: bold;">${data.is_paid ? 'PAGADO' : 'PENDIENTE'}</td>
                </tr>
            `;
            if (!data.is_paid) {
                totalPending += data.total;
            }
        });
        
        htmlContent += `
                </tbody>
            </table>
        `;
        
        if (totalPending > 0) {
            htmlContent += `
                <div style="background: #ffe6e6; padding: 15px; border-radius: 8px; margin-top: 20px; border: 2px solid #ff6b6b;">
                    <h3 style="color: #dc3545; margin-top: 0;">Total pendiente de cobro: ₡${totalPending}</h3>
                </div>
            `;
        }
    } else {
        htmlContent += `<p style="margin-top: 20px; color: #666;">No hay selecciones registradas</p>`;
    }
    
    htmlContent += `
        </div>
    `;

    // Crear ventana para imprimir
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>RIFA: ${config.name}</title>
            <style>
                @media print {
                    body { margin: 0; }
                }
            </style>
        </head>
        <body>
            ${htmlContent}
            <script>
                window.onload = function() {
                    window.print();
                }
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}
