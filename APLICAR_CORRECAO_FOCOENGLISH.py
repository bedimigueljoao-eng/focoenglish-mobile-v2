from pathlib import Path
import re, subprocess, sys

HTML = Path('app/src/main/assets/index.html')
JAVA = Path('app/src/main/java/com/focoenglish/mobile/MainActivity.java')

if not HTML.exists() or not JAVA.exists():
    raise SystemExit('ERRO: execute este ficheiro na raiz do repositorio focoenglish-mobile-v2.')

html = HTML.read_text(encoding='utf-8')
java = JAVA.read_text(encoding='utf-8')

# 1) Android: confirmacoes JS e curriculo direto.
if 'import android.webkit.WebChromeClient;' not in java and 'import android.webkit.*;' not in java:
    java = java.replace('import android.webkit.WebViewClient;', 'import android.webkit.WebViewClient;\nimport android.webkit.WebChromeClient;')
if 'setWebChromeClient' not in java:
    java = java.replace('web.setWebViewClient(', 'web.setWebChromeClient(new WebChromeClient());\n        web.setWebViewClient(', 1)
if 'getCurriculum()' not in java:
    marker = 'public class Bridge {' if 'public class Bridge {' in java else 'public class Bridge{'
    method = '''\n        @JavascriptInterface\n        public String getCurriculum() {\n            return readAssetFile("curriculum.json");\n        }\n'''
    if marker not in java:
        raise SystemExit('ERRO: nao encontrei a classe Bridge no MainActivity.java.')
    java = java.replace(marker, marker + method, 1)
JAVA.write_text(java, encoding='utf-8')

# 2) Visual do botao X.
if '.sheet-close{' not in html:
    html = html.replace(
        '.handle{width:45px;height:5px;background:#dce3ee;border-radius:20px;margin:-8px auto 18px}',
        '.handle{width:45px;height:5px;background:#dce3ee;border-radius:20px;margin:-8px auto 10px}.sheet-head{display:flex;justify-content:flex-end;margin-bottom:5px}.sheet-close{width:42px;height:42px;border:0;border-radius:13px;background:#edf2f8;color:#334155;font-size:25px;line-height:1}'
    )

# 3) Modal com X, toque fora e suporte ao botao Voltar.
pattern = r"function sheet\(x\)\{.*?\}function closeSheet\(\)\{.*?\}"
replacement = '''function sheet(x){$('sheet').innerHTML=`<div class="sheet-head"><button class="sheet-close" type="button" onclick="closeSheet()" aria-label="Fechar">×</button></div>${x}`;$('modal').classList.remove('hide')}\nfunction closeSheet(){$('modal').classList.add('hide');$('sheet').innerHTML=''}\nwindow.closeOpenModal=function(){if(!$('modal').classList.contains('hide')){closeSheet();return true}return false}\n$('modal').addEventListener('click',function(e){if(e.target===this)closeSheet()});'''
if 'window.closeOpenModal' not in html:
    html, n = re.subn(pattern, replacement, html, count=1)
    if n != 1:
        raise SystemExit('ERRO: nao consegui atualizar o modal no index.html.')

# 4) Botao Cancelar nos formularios principais.
buttons = [
    ('<button class="btn full" onclick="saveCustom()">Guardar tema</button>', '<div class="actions"><button class="btn alt" type="button" onclick="closeSheet()">Cancelar</button><button class="btn grow" onclick="saveCustom()">Guardar tema</button></div>'),
    ('<button class="btn full" onclick="savePhrase()">Guardar frase</button>', '<div class="actions"><button class="btn alt" type="button" onclick="closeSheet()">Cancelar</button><button class="btn grow" onclick="savePhrase()">Guardar frase</button></div>'),
    ('<button class="btn full" onclick="saveMovie()">Guardar</button>', '<div class="actions"><button class="btn alt" type="button" onclick="closeSheet()">Cancelar</button><button class="btn grow" onclick="saveMovie()">Guardar</button></div>'),
    ('<button class="btn full" onclick="saveGoals()">Guardar metas</button>', '<div class="actions"><button class="btn alt" type="button" onclick="closeSheet()">Cancelar</button><button class="btn grow" onclick="saveGoals()">Guardar metas</button></div>'),
]
for old, new in buttons:
    html = html.replace(old, new)

# 5) Materiais: abrir, eliminar, links e PDF associados ao tema.
old_material = '''${ms.length?ms.map(m=>`<div class="row"><div class="grow"><b>${esc(m.title)}</b><div class="muted">${esc(m.type)}</div></div><button class="btn alt" onclick="openExternal('${esc(m.url)}')">Abrir</button></div>`).join(''):'<div class="empty">Nenhum material associado.</div>'}<button class="btn alt full" onclick="addLink(${id})">+ Adicionar link</button>'''
new_material = '''${ms.length?ms.map(m=>`<div class="row"><div class="grow"><b>${esc(m.title)}</b><div class="muted">${esc(m.type)}</div></div><button class="btn alt" onclick="${m.fileId?`openPdf('${m.fileId}')`:`openExternal('${esc(m.url)}')`}">Abrir</button><button class="btn red" onclick="deleteMaterial('${m.id}',${id})">Eliminar</button></div>`).join(''):'<div class="empty">Nenhum material associado.</div>'}<div class="actions"><button class="btn alt grow" onclick="addLink(${id})">+ Link / YouTube / música</button><button class="btn alt grow" onclick="addPdfForTopic(${id})">+ PDF</button></div>'''
if old_material in html:
    html = html.replace(old_material, new_material, 1)
elif 'addPdfForTopic(${id})' not in html:
    raise SystemExit('ERRO: nao encontrei a area de materiais esperada.')

html = html.replace('<option>YouTube</option><option>Website</option><option>Documento externo</option>', '<option>YouTube</option><option>Website</option><option>Áudio ou música</option><option>Documento externo</option><option>Outro material</option>')

marker = "function addPdf(){if(window.Android&&Android.choosePdf)Android.choosePdf();else note('A importação funciona dentro da aplicação Android.')}"
if 'function addPdfForTopic' not in html:
    helper = """let pendingPdfLessonId=null;\nfunction addPdfForTopic(id){pendingPdfLessonId=id;if(window.Android&&Android.choosePdf)Android.choosePdf();else note('A importação funciona dentro da aplicação Android.')}\nfunction deleteMaterial(materialId,lessonId){if(!confirm('Eliminar este material do tema?'))return;let d=data();d.materials=d.materials.filter(x=>x.id!==materialId);save(d);openTopic(lessonId);note('Material eliminado.')}\n"""
    if marker not in html:
        raise SystemExit('ERRO: nao encontrei a funcao addPdf.')
    html = html.replace(marker, helper + marker, 1)

old_save_pdf = "function savePdf(fid,name){let d=data();d.pdfs.push({id:uid(),fileId:fid,fileName:name,title:pdt.value||name,level:pdl.value,category:pdc.value,status:pds.value,created:today()});save(d);closeSheet();renderLibrary()}"
new_save_pdf = "function savePdf(fid,name){let d=data(),title=pdt.value||name,pdfId=uid();d.pdfs.push({id:pdfId,fileId:fid,fileName:name,title,level:pdl.value,category:pdc.value,status:pds.value,lessonId:pendingPdfLessonId,created:today()});if(pendingPdfLessonId)d.materials.push({id:uid(),lessonId:pendingPdfLessonId,title,type:'PDF',fileId:fid,pdfId});let lesson=pendingPdfLessonId;pendingPdfLessonId=null;save(d);closeSheet();if(lesson)openTopic(lesson);else renderLibrary();note('PDF guardado com sucesso.')}"
if old_save_pdf in html:
    html = html.replace(old_save_pdf, new_save_pdf, 1)

# 6) Carregamento seguro do curriculo, se ainda estiver no fetch simples.
old_start = "migrate();fetch('curriculum.json').then(r=>r.json()).then(x=>{CUR=x;currentId=current().id;renderHome();renderMap();renderStudy();renderLibrary();renderMore()}).catch(()=>note('Não foi possível carregar o currículo.'));"
new_start = "async function iniciarAplicacao(){try{let txt='';if(window.Android&&typeof Android.getCurriculum==='function')txt=Android.getCurriculum();CUR=txt?JSON.parse(txt):await (await fetch('curriculum.json')).json();if(!Array.isArray(CUR)||!CUR.length)throw new Error('Currículo vazio');currentId=current().id;renderHome();renderMap();renderStudy();renderLibrary();renderMore()}catch(e){console.error(e);note('Não foi possível carregar o currículo.')}}migrate();iniciarAplicacao();"
html = html.replace(old_start, new_start)

# Separadores explicitos para evitar ambiguidades no JavaScript compactado.
html = html.replace('}function ', '}\nfunction ').replace('}window.onPdfImported', '}\nwindow.onPdfImported').replace(')}function ', ')};\nfunction ')
HTML.write_text(html, encoding='utf-8')

# 7) Validacao real de sintaxe do JavaScript.
script = html.split('<script>',1)[1].rsplit('</script>',1)[0]
check = Path('/tmp/focoenglish_check.js')
check.write_text(script, encoding='utf-8')
result = subprocess.run(['node','--check',str(check)], capture_output=True, text=True)
if result.returncode != 0:
    print(result.stderr)
    raise SystemExit('ERRO: a validacao JavaScript falhou. Os backups continuam disponiveis.')

print('OK: correcoes aplicadas e JavaScript validado.')
print('Corrigido: inicio, mapa, X, Cancelar, toque fora, Reiniciar, Eliminar e materiais por tema.')
