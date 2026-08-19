from . import notes_admin
from . import notes_public, notes_import_export, notes_socketio
from routes import bp
from socketio_instance import socketio

bp.add_url_rule('/api/notes', view_func=notes_admin.list_notes, methods=['GET'])
bp.add_url_rule('/api/notes', view_func=notes_admin.create_note, methods=['POST'])
bp.add_url_rule('/api/notes/<int:note_id>', view_func=notes_admin.update_note, methods=['PUT'])
bp.add_url_rule('/api/notes/<int:note_id>', view_func=notes_admin.delete_note, methods=['DELETE'])
bp.add_url_rule('/api/notes/<int:note_id>/share', view_func=notes_admin.share_note, methods=['POST'])
bp.add_url_rule('/api/notes/<int:note_id>/unshare', view_func=notes_admin.unshare_note, methods=['POST'])
bp.add_url_rule('/api/notes/upload-image', view_func=notes_admin.upload_note_image, methods=['POST'])

# Import/export notes
bp.add_url_rule('/api/notes/export-json', view_func=notes_import_export.export_notes_json, methods=['GET'])
bp.add_url_rule('/api/notes/import-json', view_func=notes_import_export.import_notes_json, methods=['POST'])
bp.add_url_rule('/api/notes/export-pdf', view_func=notes_import_export.export_note_pdf, methods=['POST'])

# Public notes
bp.add_url_rule('/notas/publicas/<token>', view_func=notes_public.note_public_page, methods=['GET'])
bp.add_url_rule('/notas/publicas/<token>/json', view_func=notes_public.get_public_note, methods=['GET'])
bp.add_url_rule('/api/notas/publicas/<token>', view_func=notes_public.get_public_note, methods=['GET'])
bp.add_url_rule('/notas/publicas/<token>/manifest.json', view_func=notes_public.note_public_manifest, methods=['GET'])
bp.add_url_rule('/notas/publicas/<token>', view_func=notes_public.update_public_note, methods=['PUT'])
bp.add_url_rule('/notas/publicas/<token>/upload-image', view_func=notes_public.upload_public_note_image, methods=['POST'])

# Socket.IO events
socketio.on('join_note')(notes_socketio.handle_join_note)
socketio.on('leave_note')(notes_socketio.handle_leave_note)
socketio.on('note_cursor')(notes_socketio.handle_note_cursor)
socketio.on('note_edit')(notes_socketio.handle_note_edit)