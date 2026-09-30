// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
        function updateLinkFormPreview() {
            try {
                const previewContainer = document.getElementById('formPreview');
                if (!previewContainer) return;
                const sectionItems = document.querySelectorAll('#sectionsList .section-item');

                if (sectionItems.length === 0) {
                    previewContainer.innerHTML = '<div class="text-center text-muted small">Agrega secciones para ver la vista previa</div>';
                    return;
                }

                let previewHtml = '';

                sectionItems.forEach(section => {
                    const sectionId = section.id.replace('section_', '');
                    const titleInput = document.getElementById(`sectionTitle_${sectionId}`);
                    const title = titleInput ? titleInput.value : 'Sin título';

                    previewHtml += `<div class="mb-3 p-2 border rounded-2 bg-light"><h6 class="fw-bold text-orange mb-2">${title}</h6>`;

                    // Campos predeterminados
                    const cedulaCheck = document.getElementById(`section_${sectionId}_field_cedula`);
                    if (cedulaCheck && cedulaCheck.checked) {
                        previewHtml += `<div class="mb-2"><label class="small fw-bold">Cédula</label><input type="text" class="form-control form-control-sm" placeholder="Número de cédula" disabled></div>`;
                    }
                    const nombreCheck = document.getElementById(`section_${sectionId}_field_nombre`);
                    if (nombreCheck && nombreCheck.checked) {
                        previewHtml += `<div class="mb-2"><label class="small fw-bold">Nombre</label><input type="text" class="form-control form-control-sm" placeholder="Nombre completo" disabled></div>`;
                    }
                    const telefonoCheck = document.getElementById(`section_${sectionId}_field_telefono`);
                    if (telefonoCheck && telefonoCheck.checked) {
                        previewHtml += `<div class="mb-2"><label class="small fw-bold">Teléfono</label><input type="text" class="form-control form-control-sm" placeholder="Número de teléfono" disabled></div>`;
                    }
                    const fechaCheck = document.getElementById(`section_${sectionId}_field_fecha_nacimiento`);
                    if (fechaCheck && fechaCheck.checked) {
                        previewHtml += `<div class="mb-2"><label class="small fw-bold">Fecha de Nacimiento</label><input type="date" class="form-control form-control-sm" disabled></div>`;
                    }

                    // Ficha médica
                    const fichaCheck = document.getElementById(`section_${sectionId}_field_ficha_medica`);
                    if (fichaCheck && fichaCheck.checked) {
                        previewHtml += `<div class="mt-2 pt-2 border-top"><small class="fw-bold text-secondary">Ficha Médica</small>`;
                        const tipoSangreCheck = document.getElementById(`section_${sectionId}_field_tipo_sangre`);
                        if (tipoSangreCheck && tipoSangreCheck.checked) {
                            previewHtml += `<div class="mb-1"><label class="small">Tipo de Sangre</label><input type="text" class="form-control form-control-sm" disabled></div>`;
                        }
                        const alergiasCheck = document.getElementById(`section_${sectionId}_field_alergias`);
                        if (alergiasCheck && alergiasCheck.checked) {
                            previewHtml += `<div class="mb-1"><label class="small">Alergias</label><input type="text" class="form-control form-control-sm" disabled></div>`;
                        }
                        const enfermedadesCheck = document.getElementById(`section_${sectionId}_field_enfermedades`);
                        if (enfermedadesCheck && enfermedadesCheck.checked) {
                            previewHtml += `<div class="mb-1"><label class="small">Enfermedades Crónicas</label><input type="text" class="form-control form-control-sm" disabled></div>`;
                        }
                        const contactoCheck = document.getElementById(`section_${sectionId}_field_contacto_emergencia`);
                        if (contactoCheck && contactoCheck.checked) {
                            previewHtml += `<div class="mb-1"><label class="small">Contacto de Emergencia</label><input type="text" class="form-control form-control-sm" disabled></div>`;
                        }
                        previewHtml += `</div>`;
                    }

                    // Campos personalizados
                    const customFields = section.querySelectorAll('.custom-field-item');
                    customFields.forEach(field => {
                        const fieldId = field.id.replace('field_', '');
                        const typeSelect = field.querySelector('select');
                        const type = typeSelect ? typeSelect.value : 'text';
                        const nameInput = document.getElementById(`fieldName_${fieldId}`);
                        const name = nameInput ? nameInput.value : '';
                        if (name) {
                            previewHtml += `<div class="mb-2"><label class="small fw-bold">${name}</label>`;
                            if (type === 'text') {
                                previewHtml += `<input type="text" class="form-control form-control-sm" disabled>`;
                            } else if (type === 'textarea') {
                                previewHtml += `<textarea class="form-control form-control-sm" rows="2" disabled></textarea>`;
                            } else if (type === 'select') {
                                previewHtml += `<select class="form-select form-select-sm" disabled><option>Seleccionar...</option>`;
                                const options = field.querySelectorAll('#fieldOptions_' + fieldId + ' input');
                                options.forEach(opt => {
                                    if (opt.value) previewHtml += `<option>${opt.value}</option>`;
                                });
                                previewHtml += `</select>`;
                            } else if (type === 'checkbox') {
                                previewHtml += `<div class="form-check"><input class="form-check-input" type="checkbox" disabled><label class="form-check-label small">${name}</label></div>`;
                            }
                            previewHtml += `</div>`;
                        }
                    });

                    previewHtml += `</div>`;
                });

                previewContainer.innerHTML = previewHtml;
            } catch (error) {
                console.error('Error en updateLinkFormPreview:', error);
            }
        }

        function generateFormLink() {
            const select = document.getElementById('selectEventosActivos');
            const eventId = select.value;

            if (!eventId) {
                alert('Por favor selecciona un evento');
                return;
            }

            // Recopilar secciones
            const sections = [];
            const sectionItems = document.querySelectorAll('#sectionsList .section-item');

            sectionItems.forEach(section => {
                const sectionId = section.id.replace('section_', '');
                const title = document.getElementById(`sectionTitle_${sectionId}`).value || 'Sin título';

                const sectionData = {
                    title: title,
                    predeterminados: [],
                    ficha_medica: [],
                    personalizados: []
                };

                // Campos predeterminados
                if (document.getElementById(`section_${sectionId}_field_cedula`).checked) sectionData.predeterminados.push('cedula');
                if (document.getElementById(`section_${sectionId}_field_nombre`).checked) sectionData.predeterminados.push('nombre');
                if (document.getElementById(`section_${sectionId}_field_telefono`).checked) sectionData.predeterminados.push('telefono');
                if (document.getElementById(`section_${sectionId}_field_fecha_nacimiento`).checked) sectionData.predeterminados.push('fecha_nacimiento');

                // Ficha médica
                if (document.getElementById(`section_${sectionId}_field_ficha_medica`).checked) {
                    if (document.getElementById(`section_${sectionId}_field_tipo_sangre`).checked) sectionData.ficha_medica.push('tipo_sangre');
                    if (document.getElementById(`section_${sectionId}_field_alergias`).checked) sectionData.ficha_medica.push('alergias');
                    if (document.getElementById(`section_${sectionId}_field_enfermedades`).checked) sectionData.ficha_medica.push('enfermedades');
                    if (document.getElementById(`section_${sectionId}_field_contacto_emergencia`).checked) sectionData.ficha_medica.push('contacto_emergencia');
                }

                // Campos personalizados
                const customFields = section.querySelectorAll('.custom-field-item');
                customFields.forEach(field => {
                    const fieldId = field.id.replace('field_', '');
                    const type = field.querySelector('select').value;
                    const name = document.getElementById(`fieldName_${fieldId}`).value;
                    if (name) {
                        const customField = { type, name };
                        if (type === 'select') {
                            customField.options = [];
                            const options = field.querySelectorAll('#fieldOptions_' + fieldId + ' input');
                            options.forEach(opt => {
                                if (opt.value) customField.options.push(opt.value);
                            });
                        }
                        sectionData.personalizados.push(customField);
                    }
                });

                sections.push(sectionData);
            });

            // Codificar secciones en base64
            const sectionsJson = JSON.stringify(sections);
            const sectionsEncoded = btoa(unescape(encodeURIComponent(sectionsJson)));

            // Generar link
            let linkUrl;
            if (eventId === 'registro') {
                linkUrl = window.location.origin + '/registro?sections=' + sectionsEncoded;
            } else {
                const eventName = select.options[select.selectedIndex].getAttribute('data-name');
                const slug = eventName.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
                linkUrl = window.location.origin + '/inscripcion/' + slug + '-' + eventId + '?sections=' + sectionsEncoded;
            }

            document.getElementById('generatedLinkUrl').value = linkUrl;
            document.getElementById('linkResultContainer').classList.remove('d-none');
        }

        function copyGeneratedLink() {
            const input = document.getElementById('generatedLinkUrl');
            const feedback = document.getElementById('copyFeedback');
            input.select();
            input.setSelectionRange(0, 99999);
            const doFeedback = () => {
                if (feedback) {
                    feedback.classList.remove('d-none');
                    setTimeout(() => feedback.classList.add('d-none'), 2500);
                }
            };
            navigator.clipboard.writeText(input.value).then(doFeedback).catch(() => {
                document.execCommand('copy');
                doFeedback();
            });
        }
