// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
        let generadorModal;
        let sectionCounter = 0;
        let fieldCounter = 0;

        async function abrirGeneradorLinks() {
            if (!generadorModal) {
                generadorModal = new bootstrap.Modal(document.getElementById('linkGeneratorModal'));
            }
            generadorModal.show();

            const select = document.getElementById('selectEventosActivos');
            const linkContainer = document.getElementById('linkResultContainer');

            select.innerHTML = '<option value="">Buscando caminatas activas...</option>';
            linkContainer.classList.add('d-none');

            try {
                const res = await fetch('/api/get_events');
                const eventos = await res.json();

                select.innerHTML = '<option value="" selected disabled>-- Toque aquí para seleccionar --</option>';
                select.innerHTML += '<option value="registro" data-name="registro">\uD83D\uDDD2\uFE0F Solo Registrar (sin caminata)</option>';
                let opcionesValidas = 0;

                eventos.forEach(ev => {
                    if (!ev.is_sold_out) {
                        select.innerHTML += `<option value="${ev.id}" data-name="${ev.nombreLugar}">${ev.nombreLugar} - ${ev.fecha}</option>`;
                        opcionesValidas++;
                    }
                });

                if (opcionesValidas === 0) {
                    select.innerHTML = '<option value="" disabled>No hay caminatas con espacio en este momento</option>';
                }
            } catch (error) {
                select.innerHTML = '<option value="" disabled>Error de conexión al buscar caminatas.</option>';
            }
        }

        function addSection() {
            sectionCounter++;
            const container = document.getElementById('sectionsList');
            const noSectionsMsg = document.getElementById('noSectionsMsg');
            if (noSectionsMsg) noSectionsMsg.classList.add('d-none');

            const sectionHtml = `
                <div class="section-item mb-4 p-3 bg-light rounded-3" id="section_${sectionCounter}">
                    <div class="row g-2 mb-3">
                        <div class="col-md-10">
                            <input type="text" class="form-control form-control-sm fw-bold" placeholder="Título de la sección" id="sectionTitle_${sectionCounter}" oninput="updateLinkFormPreview()">
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-danger btn-sm w-100" onclick="removeSection(${sectionCounter})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="small fw-bold text-secondary">Campos predeterminados:</label>
                        <div class="row g-2 mt-1">
                            <div class="col-md-4">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_cedula" onchange="updateLinkFormPreview()">
                                    <label class="form-check-label small" for="section_${sectionCounter}_field_cedula">Cédula</label>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_nombre" onchange="updateLinkFormPreview()">
                                    <label class="form-check-label small" for="section_${sectionCounter}_field_nombre">Nombre</label>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_telefono" onchange="updateLinkFormPreview()">
                                    <label class="form-check-label small" for="section_${sectionCounter}_field_telefono">Teléfono</label>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_fecha_nacimiento" onchange="updateLinkFormPreview()">
                                    <label class="form-check-label small" for="section_${sectionCounter}_field_fecha_nacimiento">Fecha Nacimiento</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="small fw-bold text-secondary">Ficha médica:</label>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_ficha_medica" onchange="toggleFichaMedica(${sectionCounter}); updateLinkFormPreview();">
                            <label class="form-check-label small" for="section_${sectionCounter}_field_ficha_medica">Incluir ficha médica completa</label>
                        </div>
                        <div id="section_${sectionCounter}_ficha_medica_subfields" class="ms-4 d-none mt-1">
                            <div class="form-check"><input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_tipo_sangre" onchange="updateLinkFormPreview()"><label class="form-check-label small" for="section_${sectionCounter}_field_tipo_sangre">Tipo Sangre</label></div>
                            <div class="form-check"><input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_alergias" onchange="updateLinkFormPreview()"><label class="form-check-label small" for="section_${sectionCounter}_field_alergias">Alergias</label></div>
                            <div class="form-check"><input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_enfermedades" onchange="updateLinkFormPreview()"><label class="form-check-label small" for="section_${sectionCounter}_field_enfermedades">Enfermedades</label></div>
                            <div class="form-check"><input class="form-check-input" type="checkbox" id="section_${sectionCounter}_field_contacto_emergencia" onchange="updateLinkFormPreview()"><label class="form-check-label small" for="section_${sectionCounter}_field_contacto_emergencia">Contacto Emergencia</label></div>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="small fw-bold text-secondary">Campos personalizados:</label>
                        <div id="section_${sectionCounter}_customFieldsList"></div>
                        <button class="btn btn-outline-orange btn-sm mt-1" onclick="addFieldToSection(${sectionCounter})">
                            <i class="bi bi-plus"></i> Agregar campo
                        </button>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', sectionHtml);
            updateLinkFormPreview();
        }

        function removeSection(id) {
            const section = document.getElementById(`section_${id}`);
            section.remove();
            const container = document.getElementById('sectionsList');
            if (container.children.length === 0) {
                const noSectionsMsg = document.getElementById('noSectionsMsg');
                if (noSectionsMsg) noSectionsMsg.classList.remove('d-none');
            }
            updateLinkFormPreview();
        }

        function toggleFichaMedica(sectionId) {
            const subfields = document.getElementById(`section_${sectionId}_ficha_medica_subfields`);
            const checkbox = document.getElementById(`section_${sectionId}_field_ficha_medica`);
            if (checkbox.checked) {
                subfields.classList.remove('d-none');
            } else {
                subfields.classList.add('d-none');
            }
        }

        function addFieldToSection(sectionId) {
            fieldCounter++;
            const container = document.getElementById(`section_${sectionId}_customFieldsList`);

            const fieldHtml = `
                <div class="custom-field-item mb-2 p-2 bg-white rounded-2" id="field_${fieldCounter}">
                    <div class="row g-2">
                        <div class="col-md-3">
                            <select class="form-select form-select-sm" onchange="toggleLinkFieldType(${fieldCounter}, this.value); updateLinkFormPreview();">
                                <option value="text">Texto corto</option>
                                <option value="textarea">Texto largo</option>
                                <option value="select">Lista</option>
                                <option value="checkbox">Checkbox</option>
                            </select>
                        </div>
                        <div class="col-md-5">
                            <input type="text" class="form-control form-control-sm" placeholder="Nombre del campo" id="fieldName_${fieldCounter}" oninput="updateLinkFormPreview()">
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-danger btn-sm w-100" onclick="removeLinkCustomField(${fieldCounter})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div id="fieldOptions_${fieldCounter}" class="d-none mt-1">
                        <input type="text" class="form-control form-control-sm mb-1" placeholder="Opción 1" id="fieldOption_${fieldCounter}_1" oninput="updateLinkFormPreview()">
                        <input type="text" class="form-control form-control-sm mb-1" placeholder="Opción 2" id="fieldOption_${fieldCounter}_2" oninput="updateLinkFormPreview()">
                        <button class="btn btn-outline-orange btn-sm" onclick="addLinkFieldOption(${fieldCounter})">
                            <i class="bi bi-plus"></i> Agregar opción
                        </button>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', fieldHtml);
            updateLinkFormPreview();
        }

        function toggleLinkFieldType(fieldId, type) {
            const optionsDiv = document.getElementById(`fieldOptions_${fieldId}`);
            if (type === 'select') {
                optionsDiv.classList.remove('d-none');
            } else {
                optionsDiv.classList.add('d-none');
            }
        }

        function addLinkFieldOption(fieldId) {
            const container = document.getElementById(`fieldOptions_${fieldId}`);
            const optionCount = container.querySelectorAll('input').length + 1;
            const optionHtml = `
                <input type="text" class="form-control form-control-sm mb-1" placeholder="Opción ${optionCount}" id="fieldOption_${fieldId}_${optionCount}" oninput="updateLinkFormPreview()">
            `;
            container.insertAdjacentHTML('beforeend', optionHtml);
            updateLinkFormPreview();
        }

        function removeLinkCustomField(id) {
            const field = document.getElementById(`field_${id}`);
            field.remove();
            updateLinkFormPreview();
        }

