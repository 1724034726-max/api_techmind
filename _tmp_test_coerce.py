from app.services.editor_ai_service import _coerce_expand_md, _partial_json_string_field

partial = '{"appendix_md":"## Hi\\n\\nworld'
print("partial:", repr(_partial_json_string_field(partial, "appendix_md")))
print("full:", repr(_coerce_expand_md('{"appendix_md":"## Done\\n\\nok"}')))
print("plain:", repr(_coerce_expand_md("## plain\n\nmd")))
