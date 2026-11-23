
/**
 * GeoResiduos Bogotá | Fase 4 - Cliente con API persistente
 * Cliente conectado al servidor de pruebas. NO es un canal oficial de la UAESP.
 * © 2026 Proyecto aplicado de Ingeniería de Sistemas - ejemplo académico.
 */
(function () {
  'use strict';

  const categories = ['Residuos ordinarios','Escombros (RCD)','Residuos voluminosos','Residuos mixtos','Otros'];
  let records = [];
  let csrf = '';
  let adminAuthed = false;
  let adminConfigured = false;
  let activeView = 'inicio';
  let map = null;
  let formMap = null;
  let allMapMarkers = [];
  let chosenMarker = null;
  let formMarker = null;
  let photoData = '';
  let toastTimer = null;
  let mapSelection = '';

  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));
  const icon = id => `<svg aria-hidden="true"><use href="#ic-${id}"/></svg>`;
  const escapeHTML = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const dateLabel = value => {
    if (!value) return 'Sin fecha';
    const d = new Date(value+'T12:00:00');
    return isNaN(d) ? value : d.toLocaleDateString('es-CO',{day:'2-digit',month:'short',year:'numeric'}).replace(/\./g,'');
  };
  const localDate = () => { const d=new Date(); const p=n=>String(n).padStart(2,'0'); return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`; };
  const newest = list => [...list].sort((a,b)=>b.date.localeCompare(a.date)||b.id.localeCompare(a.id));
  async function api(url,options={}){
    const config={credentials:'same-origin',...options};
    config.headers={'Content-Type':'application/json',...(config.headers||{})};
    if(config.method && config.method.toUpperCase()!=='GET')config.headers['X-CSRF-Token']=csrf;
    let response;
    try { response=await fetch(url,config); }
    catch(e){throw new Error('No hay conexión con el servidor. Abre la aplicación desde http://127.0.0.1:8000.');}
    let data={};try{data=await response.json();}catch(e){}
    if(!response.ok){
      const detail=Array.isArray(data.detail)?data.detail.map(x=>x.msg).join('; '):data.detail;
      throw new Error(detail || ('Error '+response.status));
    }
    return data;
  }
  async function refreshFromServer(){
    try{
      const data=await api('/api/reports');records=data.items||[];
      refreshUI();
    }catch(e){showToast(e.message,true)}
  }
  async function initialize(){
    try{
      const s=await api('/api/session');csrf=s.csrf;adminAuthed=s.admin;adminConfigured=s.adminConfigured;
      updateAdminPanels();await refreshFromServer();
    }catch(e){showToast(e.message,true)}
  }
  function updateAdminPanels(){
    $('#adminLoginPane').hidden=adminAuthed;
    $('#adminPrivate').hidden=!adminAuthed;
    $('#adminNotice').textContent=adminAuthed?'Sesión administrativa activa. Los cambios se guardan en la base de datos.':(adminConfigured?'Ingresa la contraseña para actualizar estados de revisión.':'El administrador debe configurarse en el servidor. La consulta pública está disponible sin contraseña.');
    $('#adminLogout').hidden=!adminAuthed;
    if(adminAuthed)renderAdmin();
  }
  function showToast(message,error=false){const el=$('#toast');el.textContent=message;el.classList.toggle('error',error);el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3900);}
  function counts(){return {all:records.length,pending:records.filter(r=>r.status==='Pendiente').length,review:records.filter(r=>r.status==='En revisión').length,closed:records.filter(r=>r.status==='Cerrado').length,localities:new Set(records.map(r=>r.locality)).size};}
  function badge(status){const kind=status==='En revisión'?'review':status==='Cerrado'?'closed':'';return `<span class="badge-status ${kind}">${escapeHTML(status)}</span>`;}
  function closeMobile(){ $('#sidebar').classList.remove('open');$('#mobileOverlay').classList.remove('show'); }
  function showView(next){
    if (!['inicio','registrar','mapa','reportes','admin'].includes(next))return;
    activeView=next;
    $$('.view').forEach(el=>el.classList.toggle('active',el.id===`view-${next}`));
    $$('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.view===next));
    const names={inicio:'Panel general',registrar:'Nuevo reporte',mapa:'Mapa de puntos',reportes:'Consultar reportes',admin:'Administración'};
    $('#crumbCurrent').textContent=names[next];
    closeMobile();
    window.scrollTo({top:0,behavior:'instant'});
    refreshUI();
    if(next==='mapa')setTimeout(initMainMap,120);
    if(next==='registrar')setTimeout(initFormMap,120);
    if(next==='admin')updateAdminPanels();
  }
  function refreshUI(){renderHome();renderReports();renderAdmin();renderMapList();}

  function renderHome(){
    const c=counts();
    const vals=[
      {title:'Reportes registrados',count:c.all,note:'En la base de datos',ic:'file',tone:''},
      {title:'Pendientes',count:c.pending,note:'En espera de revisión',ic:'clock',tone:'gold'},
      {title:'En revisión',count:c.review,note:'Según registros almacenados',ic:'target',tone:'blue'},
      {title:'Localidades registradas',count:c.localities,note:'De los registros disponibles',ic:'map',tone:'purple'}
    ];
    $('#statGrid').innerHTML=vals.map(x=>`<article class="stat-card"><div class="stat-top"><span>${x.title}</span><span class="stat-icon ${x.tone}">${icon(x.ic)}</span></div><div class="stat-number">${x.count.toLocaleString('es-CO')}</div><div class="stat-note">${escapeHTML(x.note)}</div></article>`).join('');
    $('#recentReports').innerHTML=newest(records).slice(0,4).map(r=>`<div class="recent-row" data-detail="${escapeHTML(r.id)}" role="button" tabindex="0"><div class="recent-icon">${icon('pin')}</div><div class="recent-meta"><strong>${escapeHTML(r.locality)} · ${escapeHTML(r.category)}</strong><span>${escapeHTML(r.id)} &nbsp;•&nbsp; ${dateLabel(r.date)}</span></div>${badge(r.status)}</div>`).join('')||'<div class="empty-state">No existen registros.</div>';
    const max=Math.max(...categories.map(cat=>records.filter(r=>r.category===cat).length),1);
    $('#categoryBars').innerHTML=categories.map(cat=>{let n=records.filter(r=>r.category===cat).length;return `<div class="bar-row"><div class="bar-top"><span>${escapeHTML(cat)}</span><strong>${n}</strong></div><div class="bar-track"><div class="bar-fill" style="width:${100*n/max}%"></div></div></div>`}).join('');
    $('#todayText').textContent=new Date().toLocaleDateString('es-CO',{day:'numeric',month:'long',year:'numeric'});
  }

  function filteredReports(){
    const term=$('#reportSearch').value.trim().toLowerCase();
    const cat=$('#filterCategory').value;
    const status=$('#filterStatus').value;
    return newest(records).filter(r=>(!cat||r.category===cat)&&(!status||r.status===status)&&(!term||`${r.id} ${r.description} ${r.locality} ${r.category}`.toLowerCase().includes(term)));
  }
  function renderReports(){
    const c=counts(); $('#listTotal').textContent=c.all;$('#listReview').textContent=c.review;$('#listPending').textContent=c.pending;
    const rows=filteredReports();
    $('#reportsTbody').innerHTML=rows.map(r=>`<tr><td><div class="report-id">${escapeHTML(r.id)}</div><div class="report-sub">${escapeHTML(r.description)}</div></td><td>${escapeHTML(r.locality)}</td><td><span class="cat-tag">${escapeHTML(r.category)}</span></td><td>${dateLabel(r.date)}</td><td>${badge(r.status)}</td><td><button class="table-act" aria-label="Ver detalle de ${escapeHTML(r.id)}" title="Ver detalle" data-detail="${escapeHTML(r.id)}">${icon('eye')}</button></td></tr>`).join('')||`<tr><td colspan="6"><div class="empty-state">${icon('search')}<strong>No se encontraron reportes</strong><p>Prueba otros filtros o crea un registro.</p></div></td></tr>`;
    $('#tableCount').textContent=`${rows.length} de ${records.length} reportes`;
  }
  function renderAdmin(){
    const c=counts();
    $('#adminStats').innerHTML=[
      {name:'Pendientes de revisión',count:c.pending,tone:'gold',ic:'clock'},
      {name:'En revisión',count:c.review,tone:'blue',ic:'target'},
      {name:'Cerrados',count:c.closed,tone:'',ic:'check'}
    ].map(o=>`<div class="admin-stat"><div class="stat-icon ${o.tone}">${icon(o.ic)}</div><div><strong>${o.count}</strong><span>${o.name}</span></div></div>`).join('');
    $('#adminTbody').innerHTML=newest(records).map(r=>`<tr><td><div class="report-id">${escapeHTML(r.id)}</div><div class="report-sub">${escapeHTML(r.description)}</div></td><td>${escapeHTML(r.locality)}</td><td>${escapeHTML(r.category)}</td><td>${dateLabel(r.date)}</td><td><select class="admin-select" data-update="${escapeHTML(r.id)}" aria-label="Cambiar estado de ${escapeHTML(r.id)}">${['Pendiente','En revisión','Cerrado'].map(v=>`<option ${v===r.status?'selected':''}>${v}</option>`).join('')}</select></td><td><button class="table-act" data-detail="${escapeHTML(r.id)}" title="Ver detalle" aria-label="Ver detalle">${icon('eye')}</button></td></tr>`).join('')||'<tr><td colspan="6">No hay reportes para administrar.</td></tr>';
  }
  function mapFiltered(){const cat=$('#mapCategory').value;return newest(records).filter(r=>!cat||cat===r.category);}
  function renderMapList(){
    const entries=mapFiltered();$('#mapTotal').textContent=entries.length;
    $('#mapReportList').innerHTML=entries.map(r=>`<button class="map-list-row ${r.id===mapSelection?'selected':''}" data-locate="${escapeHTML(r.id)}"><div class="recent-icon">${icon('pin')}</div><div><strong>${escapeHTML(r.locality)} · ${escapeHTML(r.category)}</strong><span>${escapeHTML(r.id)}<br/>${dateLabel(r.date)}</span></div></button>`).join('')||'<div class="empty-state">No hay puntos con este filtro.</div>';
    if(activeView==='mapa')syncMainMarkers();
  }
  // Cartografía sin restricciones de teselas OSM: OpenFreeMap + MapLibre.
  // Cuando no hay conexión o el proveedor no responde, se utiliza el plano esquemático local.
  const MAP_STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const offlineBounds = {minLat:4.50,maxLat:4.85,minLng:-74.25,maxLng:-73.98};
  function offlinePoint(lat,lng){
    const x=Math.max(7,Math.min(93,((lng-offlineBounds.minLng)/(offlineBounds.maxLng-offlineBounds.minLng))*100));
    const y=Math.max(9,Math.min(89,((offlineBounds.maxLat-lat)/(offlineBounds.maxLat-offlineBounds.minLat))*100));
    return {x,y};
  }
  function drawOfflinePin(container,lat,lng){
    const prev=container.querySelector('.form-offline-pin');if(prev)prev.remove();
    if(!Number.isFinite(lat)||!Number.isFinite(lng))return;
    const {x,y}=offlinePoint(lat,lng);
    const pin=document.createElement('span');pin.className='form-offline-pin';pin.style.left=x+'%';pin.style.top=y+'%';pin.title='Ubicación seleccionada (aproximada)';container.appendChild(pin);
  }
  function fallbackMap(container,items,isForm=false){
    // Un plano ilustrativo, NO una cartografía oficial ni una fuente para decidir coordenadas exactas.
    container.innerHTML=`<div class="offline-illustration" aria-hidden="true">
      <svg viewBox="0 0 1000 540" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
        <rect width="1000" height="540" fill="#e9f1eb"/>
        <path d="M0 83 Q155 25 350 95 T715 96 T1000 74 V0 H0Z" fill="#d9e9d7"/>
        <path d="M805 0 Q738 83 786 154 T775 329 T897 540 H1000 V0Z" fill="#d0e4d5"/>
        <path d="M0 405 Q190 319 296 391 T628 409 T1000 395 V540 H0Z" fill="#deecdf"/>
        <path d="M-50 145 Q175 211 281 147 T546 201 T1020 142" fill="none" stroke="#fff" stroke-width="29" stroke-linecap="round"/>
        <path d="M-50 145 Q175 211 281 147 T546 201 T1020 142" fill="none" stroke="#d1dcd7" stroke-width="2"/>
        <path d="M102 -30 Q225 177 401 274 T739 570" fill="none" stroke="#fff" stroke-width="26" stroke-linecap="round"/>
        <path d="M102 -30 Q225 177 401 274 T739 570" fill="none" stroke="#cfdad6" stroke-width="2"/>
        <path d="M-80 375 Q110 261 294 299 T658 254 T1042 330" fill="none" stroke="#fff" stroke-width="24" stroke-linecap="round"/>
        <path d="M-80 375 Q110 261 294 299 T658 254 T1042 330" fill="none" stroke="#cfdad6" stroke-width="2"/>
        <path d="M604 -40 Q562 142 641 229 T611 557" fill="none" stroke="#fff" stroke-width="18" stroke-linecap="round"/>
        <path d="M604 -40 Q562 142 641 229 T611 557" fill="none" stroke="#cfdad6" stroke-width="2"/>
        <path d="M272 5 Q319 143 238 271 T318 551" fill="none" stroke="#fff" stroke-width="13" stroke-linecap="round"/>
        <path d="M785 18 Q637 149 712 281 T867 561" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round"/>
        <path d="M470 -30 Q419 105 494 231 T477 548" fill="none" stroke="#fff" stroke-width="13" stroke-linecap="round"/>
        <path d="M19 256 Q223 222 451 379 T944 468" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round"/>
        <path d="M379 25 Q424 135 361 241 T361 535" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
        <path d="M698 46 Q697 159 524 332 T352 553" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
        <g fill="#759889" font-family="Arial,sans-serif" font-weight="600" font-size="17" opacity=".78">
          <text x="356" y="111">Suba</text><text x="660" y="91">Usaquén</text>
          <text x="624" y="204">Chapinero</text><text x="235" y="245">Engativá</text>
          <text x="276" y="366">Fontibón</text><text x="458" y="288">Teusaquillo</text>
          <text x="257" y="467">Kennedy</text><text x="367" y="516">Bosa</text>
          <text x="642" y="412">San Cristóbal</text>
        </g>
      </svg>
    </div><div class="offline-map-head"><span class="offline-dot"></span> Plano ilustrativo de Bogotá</div>
    <span class="map-fallback-watermark">Sin cartografía en línea · Ubicaciones aproximadas</span>`;
    if(isForm){
      const label=document.createElement('span');label.className='offline-form-help';label.textContent='Haz clic en el plano para ubicar un punto de forma aproximada';container.appendChild(label);
      container.onclick=event=>{
        if(!event.target.closest('.offline-illustration')&&!event.target.closest('.offline-map-head'))return;
        const rect=container.getBoundingClientRect();
        const xx=Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width));
        const yy=Math.max(0,Math.min(1,(event.clientY-rect.top)/rect.height));
        const lng=offlineBounds.minLng+xx*(offlineBounds.maxLng-offlineBounds.minLng);
        const lat=offlineBounds.maxLat-yy*(offlineBounds.maxLat-offlineBounds.minLat);
        $('#latitude').value=lat.toFixed(6);$('#longitude').value=lng.toFixed(6);
        drawOfflinePin(container,lat,lng);
      };
      if($('#latitude').value&&$('#longitude').value)drawOfflinePin(container,Number($('#latitude').value),Number($('#longitude').value));
      return;
    }
    container.onclick=null;
    for(const r of items){
      const {x,y}=offlinePoint(r.lat,r.lng);
      const el=document.createElement('button');el.type='button';el.className='fake-marker'+(r.id===mapSelection?' selected':'');
      el.style.left=x+'%';el.style.top=y+'%';el.title=r.locality+' · '+r.id;
      el.setAttribute('aria-label','Ver reporte '+r.id);
      el.onclick=()=>locateReport(r.id);
      container.appendChild(el);
    }
  }
  function mapSupported(){
    return !!(window.maplibregl&&typeof maplibregl.Map==='function'&&typeof maplibregl.supported==='function'&&maplibregl.supported());
  }
  function mapUnavailable(which){
    const main=which==='main';const old=main?map:formMap;
    if(main){map=null;allMapMarkers=[];}else{formMap=null;formMarker=null;}
    if(old){try{old.remove();}catch(e){/* Recurso ya liberado */}}
    const node=main?$('#mainMap'):$('#formMap');
    fallbackMap(node,main?mapFiltered():[],!main);
  }
  function initMainMap(){
    if(activeView!=='mapa')return;
    if(map){try{map.resize();}catch(e){}return;}
    if(!mapSupported()){mapUnavailable('main');return;}
    const node=$('#mainMap');node.innerHTML='';
    try{
      const instance=new maplibregl.Map({container:node,style:MAP_STYLE,center:[-74.105,4.655],zoom:10.65,attributionControl:true,renderWorldCopies:false});
      map=instance;
      instance.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-left');
      let loaded=false;
      instance.on('load',()=>{if(map!==instance)return;loaded=true;syncMainMarkers();instance.resize();});
      instance.on('error',()=>{if(map===instance&&!loaded)setTimeout(()=>{if(map===instance&&!loaded)mapUnavailable('main');},100);});
      setTimeout(()=>{if(map===instance&&!loaded)mapUnavailable('main');},8500);
    }catch(e){mapUnavailable('main');}
  }
  function syncMainMarkers(){
    const shown=mapFiltered();
    if(!map){if(activeView==='mapa')fallbackMap($('#mainMap'),shown);return;}
    if(!map.loaded())return;
    allMapMarkers.forEach(x=>{try{x.marker.remove()}catch(e){}});allMapMarkers=[];
    for(const r of shown){
      const pin=document.createElement('div');pin.className='map-dot'+(r.id===mapSelection?' selected':'');
      pin.title=r.locality+' · '+r.id;
      const body=`<strong>${escapeHTML(r.locality)}</strong><span>${escapeHTML(r.category)}</span><br/><small>${escapeHTML(r.id)} · ${r.demo?'Datos ficticios':'Reporte del prototipo'}</small>`;
      const popup=new maplibregl.Popup({offset:19}).setHTML(body);
      const marker=new maplibregl.Marker({element:pin,anchor:'center'}).setLngLat([r.lng,r.lat]).setPopup(popup).addTo(map);
      pin.addEventListener('click',()=>{mapSelection=r.id;renderMapList();});
      allMapMarkers.push({id:r.id,marker});
    }
  }
  function locateReport(id){
    const r=records.find(x=>x.id===id);if(!r)return;
    mapSelection=id;renderMapList();
    if(map){map.flyTo({center:[r.lng,r.lat],zoom:13,essential:true});const entry=allMapMarkers.find(x=>x.id===id);if(entry)entry.marker.togglePopup();}
    else fallbackMap($('#mainMap'),mapFiltered());
  }
  function initFormMap(){
    if(activeView!=='registrar')return;
    if(formMap){try{formMap.resize()}catch(e){}return;}
    if(!mapSupported()){mapUnavailable('form');return;}
    const node=$('#formMap');node.innerHTML='';node.onclick=null;
    try{
      const instance=new maplibregl.Map({container:node,style:MAP_STYLE,center:[-74.10,4.65],zoom:10.8,attributionControl:true,renderWorldCopies:false});
      formMap=instance;
      instance.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-left');
      let loaded=false;
      instance.on('load',()=>{if(formMap!==instance)return;loaded=true;syncFormMarker();instance.resize();});
      instance.on('error',()=>{if(formMap===instance&&!loaded)setTimeout(()=>{if(formMap===instance&&!loaded)mapUnavailable('form');},100);});
      setTimeout(()=>{if(formMap===instance&&!loaded)mapUnavailable('form');},8500);
      instance.on('click',e=>{
        $('#latitude').value=e.lngLat.lat.toFixed(6);
        $('#longitude').value=e.lngLat.lng.toFixed(6);
        syncFormMarker();
      });
    }catch(e){mapUnavailable('form');}
  }
  function syncFormMarker(){
    if(!formMap){
      if(activeView==='registrar'&&$('#formMap').querySelector('.offline-illustration')&&$('#latitude').value&&$('#longitude').value){
        drawOfflinePin($('#formMap'),Number($('#latitude').value),Number($('#longitude').value));
      }
      return;
    }
    if(formMarker){formMarker.remove();formMarker=null;}
    const lat=Number($('#latitude').value),lng=Number($('#longitude').value);
    if(!Number.isFinite(lat)||!Number.isFinite(lng)||!$('#latitude').value||!$('#longitude').value)return;
    const pin=document.createElement('div');pin.className='form-pin';
    formMarker=new maplibregl.Marker({element:pin,anchor:'center'}).setLngLat([lng,lat]).addTo(formMap);
  }
  function modalOpen(id){
    const r=records.find(x=>x.id===id);if(!r)return;
    $('#detailTitle').textContent=r.id;
    $('#modalBody').innerHTML=`<div class="modal-content"><p class="detail-description">${escapeHTML(r.description)}</p><div class="detail-rows"><div><span>Localidad</span><strong>${escapeHTML(r.locality)}</strong></div><div><span>Categoría</span><strong>${escapeHTML(r.category)}</strong></div><div><span>Fecha del reporte</span><strong>${dateLabel(r.date)}</strong></div><div><span>Estado de revisión</span>${badge(r.status)}</div><div><span>Latitud</span><strong>${Number(r.lat).toFixed(6)}</strong></div><div><span>Longitud</span><strong>${Number(r.lng).toFixed(6)}</strong></div></div>${r.demo?'<div class="notice warning" style="margin-top:20px">Este reporte es ficticio y se incluye únicamente como ejemplo.</div>':''}${r.photo&&/^(\/api\/reports\/RPT-\d{6,}\/photo|\/uploads\/[a-f0-9]{32}\.webp)$/.test(r.photo)?`<img class="detail-photo" src="${escapeHTML(r.photo)}" alt="Fotografía aportada en el reporte" />`:''}</div>`;
    $('#detailModal').hidden=false;
  }
  function modalClose(){$('#detailModal').hidden=true;}
  async function submitReport(event){
    event.preventDefault();
    const description=$('#description').value.trim();
    const category=$('#category').value;
    const locality=$('#locality').value;
    const date=$('#reportDate').value;
    const lat=Number($('#latitude').value),lng=Number($('#longitude').value);
    if(description.length<12){showToast('Escribe una descripción de al menos 12 caracteres.',true);$('#description').focus();return;}
    if(!category||!locality||!date){showToast('Completa la categoría, localidad y fecha.',true);return;}
    if(!$('#latitude').value||!$('#longitude').value||!Number.isFinite(lat)||!Number.isFinite(lng)||lat<4.35||lat>4.9||lng< -74.3||lng> -73.85){showToast('Ingresa coordenadas válidas para el área de Bogotá.',true);return;}
    const btn=$('#reportForm button[type=submit]');btn.disabled=true;
    try{
      const result=await api('/api/reports',{method:'POST',body:JSON.stringify({description,category,locality,date,lat,lng,photo:photoData||null})});
      $('#reportForm').reset();$('#reportDate').value=localDate();$('#charCount').textContent='0/500';photoData='';$('#photoPreview').hidden=true;$('#uploadTitle').textContent='Haz clic para seleccionar una imagen';$('#uploadHelp').textContent='PNG, JPG o WEBP · máximo 1 MB';syncFormMarker();
      await refreshFromServer();
      showView('reportes');showToast(`Reporte ${result.item.id} guardado en la base de datos.`);
    }catch(e){showToast(e.message,true)}finally{btn.disabled=false}
  }
  function uploadImage(input){
    const file=input.files?.[0];
    if(!file){photoData='';return;}
    if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>1024*1024){input.value='';photoData='';showToast('Usa PNG, JPG o WEBP de máximo 1 MB.',true);return;}
    const reader=new FileReader();reader.onload=()=>{
      photoData=String(reader.result||'');$('#photoPreview').src=photoData;$('#photoPreview').hidden=false;
      $('#uploadTitle').textContent=file.name;$('#uploadHelp').textContent='Imagen lista para guardar en el servidor';
    };reader.readAsDataURL(file);
  }
  function exportCSV(){
    const list=filteredReports();if(!list.length){showToast('No hay registros para exportar.',true);return;}
    const titles=['ID','Fecha','Localidad','Categoria','Descripcion','Latitud','Longitud','Estado','Simulado'];
    const safeCell=value=>{let s=String(value??'');if(/^[=+@-]/.test(s)&&isNaN(Number(s)))s="'"+s;return `"${s.replace(/"/g,'""')}"`;};
    const lines=[titles,...list.map(r=>[r.id,r.date,r.locality,r.category,r.description,r.lat,r.lng,r.status,r.demo?'Sí':'No'])];
    const blob=new Blob(['\uFEFF'+lines.map(row=>row.map(safeCell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='GeoResiduos_Bogota_reportes_demo.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);showToast('Archivo CSV exportado.');
  }
  async function seedDemo(){
    if(!adminAuthed){showToast('Inicia sesión para cargar los ejemplos.',true);return;}
    try{const r=await api('/api/admin/seed-demo',{method:'POST',body:'{}'});await refreshFromServer();showToast(r.inserted?`Se cargaron ${r.inserted} reportes ficticios.`:'Los reportes ficticios ya estaban cargados.');}
    catch(e){showToast(e.message,true)}
  }
  async function updateStatus(id,newStatus){
    try{await api('/api/admin/reports/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify({status:newStatus})});await refreshFromServer();showToast(`Estado de ${id}: ${newStatus}`);}
    catch(e){await refreshFromServer();showToast(e.message,true)}
  }
  async function adminLogin(e){
    e.preventDefault();
    try{await api('/api/admin/login',{method:'POST',body:JSON.stringify({password:$('#adminPassword').value})});
      $('#adminPassword').value='';adminAuthed=true;updateAdminPanels();showToast('Sesión administrativa iniciada.');}
    catch(e){showToast(e.message,true)}
  }
  async function adminLogout(){
    try{await api('/api/admin/logout',{method:'POST',body:'{}'});adminAuthed=false;updateAdminPanels();showToast('Sesión cerrada.');}
    catch(e){showToast(e.message,true)}
  }

  // Interacciones mediante delegación para componentes que se re-renderizan.
  document.addEventListener('click',event=>{
    const link=event.target.closest('[data-view]');if(link){showView(link.dataset.view);return;}
    const detail=event.target.closest('[data-detail]');if(detail){modalOpen(detail.dataset.detail);return;}
    const locate=event.target.closest('[data-locate]');if(locate){locateReport(locate.dataset.locate);return;}
    if(event.target.closest('[data-close="modal"]'))modalClose();
  });
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape')modalClose();
    if(event.key==='Enter'&&event.target.matches('.recent-row[data-detail]'))modalOpen(event.target.dataset.detail);
  });
  document.addEventListener('change',event=>{
    const update=event.target.closest('[data-update]');if(update)updateStatus(update.dataset.update,event.target.value);
  });
  ['#reportSearch','#filterCategory','#filterStatus'].forEach(sel=>$(sel).addEventListener(sel==='#reportSearch'?'input':'change',renderReports));
  $('#mapCategory').addEventListener('change',renderMapList);
  $('#reportForm').addEventListener('submit',submitReport);
  $('#reportForm').addEventListener('reset',()=>setTimeout(()=>{$('#charCount').textContent='0/500';$('#reportDate').value=localDate();photoData='';$('#photoPreview').hidden=true;$('#uploadTitle').textContent='Haz clic para seleccionar una imagen';$('#uploadHelp').textContent='PNG, JPG o WEBP · máximo 1 MB';syncFormMarker();},10));
  $('#description').addEventListener('input',e=>$('#charCount').textContent=`${e.target.value.length}/500`);
  $('#photo').addEventListener('change',e=>uploadImage(e.target));
  ['#latitude','#longitude'].forEach(s=>$(s).addEventListener('change',()=>{syncFormMarker();if(formMap&&$('#latitude').value&&$('#longitude').value)formMap.flyTo({center:[Number($('#longitude').value),Number($('#latitude').value)],essential:true});}));
  $('#exportCsv').addEventListener('click',exportCSV);
  $('#resetDemo').addEventListener('click',seedDemo);
  $('#adminLoginForm').addEventListener('submit',adminLogin);
  $('#adminLogout').addEventListener('click',adminLogout);
  $('#modalClose').addEventListener('click',modalClose);
  $('#modalDone').addEventListener('click',modalClose);
  $('#mobileMenu').addEventListener('click',()=>{$('#sidebar').classList.add('open');$('#mobileOverlay').classList.add('show');});
  $('#mobileOverlay').addEventListener('click',closeMobile);
  $('#reportDate').value=localDate();
  refreshUI();
  initialize();
})();

