"use strict";
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const yuan = (v) => `¥${(v / 100).toFixed(2)}`;
const buddyEvent=(event,payload={})=>window.dispatchEvent(new CustomEvent('mcd:buddy',{detail:{event,payload}}));
const state = {mode:"demo",case:"coupon",csrf:"",configured:false,products:[],coupons:[],selected:[],coupon:"",store:null,category:"全部",rev:0,busy:false,suggestions:[],customDemo:null,lastResult:null};
const icon = (name) => {
 const coffee = /咖|茶|饮|水|可乐|雪碧|美式|拿铁|奶铁/.test(name);
 return coffee ? '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M16 18h32l-4 38H21z" fill="#f3e7d0"/><path d="M19 27h26l-2 17H21z" fill="#75422b"/><path d="M13 16h38v5H13z" fill="#c79150"/><path d="M32 17l5-13h4l-5 13z" fill="#bc4d32"/><path d="M22 27l7 6 6-7 6 6" fill="none" stroke="#b78d63" stroke-width="4"/></svg>' : '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M8 28c1-13 10-21 24-21s24 8 24 21" fill="#eab34d"/><path d="M9 29h46l-4 8H13z" fill="#79a047"/><path d="M9 37h46v8H9z" fill="#81412c"/><path d="M10 44h44l-6 6H16z" fill="#f0ba37"/><path d="M10 51h44c-2 7-10 9-22 9s-20-2-22-9" fill="#dfa244"/><g stroke="#fff0c7" stroke-width="2" stroke-linecap="round"><path d="M22 17l3-1M35 14l3 1M43 22l3 1M29 24l3-1"/></g></svg>';
};
function message(msg, busy=false){if(msg)buddyEvent(busy?'busy':'error');$("message").hidden=!msg;$("message").innerHTML=busy ? `<span class="busy-indicator"></span>${esc(msg)}` : esc(msg);}
function stale(){state.lastResult=null;state.rev++;$("result").hidden=true;$("suggestion-panel").hidden=true;}
async function api(path, body){
 if(window.__OFFLINE_DEMOS){
  if(path==='/api/status')return {configured:false,csrf:''};
  if(path.startsWith('/api/demo?')){
   const params=new URLSearchParams(path.split('?')[1]);const rawBudget=params.get('budget')||'';const budget=Number(rawBudget);
   if(!rawBudget.trim()||!Number.isFinite(budget)||budget<0||Math.abs(budget*100-Math.round(budget*100))>0.000001)throw Error('请输入有效预算，最多两位小数');
   return repriceDemo(window.__OFFLINE_DEMOS[params.get('case')||'coupon'],budget);

  }
  if(path==='/api/demo-suggest'){
   const source=structuredClone(window.__OFFLINE_SUGGESTIONS);const raw=String(body.budget??'');const budget=Number(raw);
   if(!raw.trim()||!Number.isFinite(budget)||budget<0||Math.abs(budget*100-Math.round(budget*100))>0.000001)throw Error('请输入有效预算，最多两位小数');
   source.options=source.options.filter(o=>(!body.anchor||o.products.includes(body.anchor))&&(body.drink==='any'||(body.drink==='coffee'&&o.products.includes('507411'))||(body.drink==='tea'&&o.products.includes('3505'))));
   for(const o of source.options){
    o.comparison=repriceDemo(o.comparison,budget);
    if(!body.coupon){o.coupon='';o.coupon_applied=false;o.comparison.result.results=o.comparison.result.results.slice(0,1);o.payable_fen=o.comparison.result.results[0].payable_fen;}
    o.comparison=repriceDemo(o.comparison,budget);
    o.within_budget=o.payable_fen<=Math.round(budget*100);o.over_budget_fen=Math.max(0,o.payable_fen-Math.round(budget*100));
   }
   source.options.sort((a,b)=>a.payable_fen-b.payable_fen);source.tested=source.options.length;source.successful=source.options.length;source.budget_fen=Math.round(budget*100);source.anchor=body.anchor;return source;
  }
  throw Error('这是离线预览，实时查询请启动本地可视化版本。');
 }
 const options=body?{method:"POST",headers:{"Content-Type":"application/json","X-Local-CSRF":state.csrf},body:JSON.stringify(body)}:{};
 const r=await fetch(path, options);const d=await r.json();if(!r.ok)throw Error(d.error||"请求未完成，请重试");return d;
}
function repriceDemo(document,budget){
 const doc=structuredClone(document);doc.budget_fen=Math.round(budget*100);
 for(const q of doc.result.results){q.within_budget=q.payable_fen<=doc.budget_fen;q.over_budget_fen=Math.max(0,q.payable_fen-doc.budget_fen);q.reasons=q.reasons.filter(r=>r!=='超预算');if(!q.within_budget)q.reasons.push('超预算');}
 const eligible=doc.result.results.filter(q=>q.qualified&&q.within_budget);const min=Math.min(...eligible.map(q=>q.payable_fen));
 doc.result.lowest_verified_options=eligible.filter(q=>q.payable_fen===min).map(q=>q.name);doc.result.status=eligible.length?'options_found':'no_eligible_option';return doc;
}
function selectedItems(){return state.products.filter(p=>state.selected.includes(p.id));}
function basket(){
 const items=selectedItems();const alternatives=state.mode==='demo'&&state.case==='none';
 $("basket-count").textContent=`${items.length}${alternatives?'组':'件'}`;
 document.querySelector('.basket-heading h3').textContent=alternatives?'本次比较的方案':'我的这份餐';
 $("basket-items").innerHTML=items.length?items.map(p=>`<div class="basket-line"><span>${esc(p.name)}<button class="basket-swap" data-keep="${esc(p.id)}">保留它，换另一种</button></span><span>× 1 ${state.mode==='live'?`<button class="basket-remove" data-remove="${esc(p.id)}" aria-label="移除${esc(p.name)}">×</button>`:''}</span></div>`).join(''):'<p class="menu-empty">从左侧选择想吃的单品。</p>';
 $("compare").disabled=state.busy||(state.mode==='live'&&!items.length);
 refreshPlanner();
}
function renderMenu(){
 const query=$("menu-search").value.trim().toLowerCase();
 const products=state.products.filter(p=>(state.category==='全部'||p.category===state.category)&&p.name.toLowerCase().includes(query));
 $("menu").classList.toggle('live-menu',state.mode==='live');
 $("menu").innerHTML=products.length?products.map(p=>`<button class="product ${state.selected.includes(p.id)?'selected':''}" data-product="${esc(p.id)}" aria-pressed="${state.selected.includes(p.id)}" ${state.mode==='demo'?'aria-disabled="true"':''}><span class="food-icon">${icon(p.name)}</span><span class="product-info"><h4>${esc(p.name)}</h4><p>${state.mode==='demo'?'实测案例 · 各1份':'默认规格 · 每种1份'}</p>${p.price?`<div class="item-price">¥${esc(p.price)} <span class="demo-label">${state.mode==='demo'?'当时单品价':'菜单价'}</span></div>`:''}</span><span class="plus">${state.selected.includes(p.id)?'✓':'+'}</span></button>`).join(''):'<p class="menu-empty">'+(state.mode==='live'&&!state.store?'搜索并选择门店后，这里会显示菜单。':'没有找到对应餐品，试试其他关键词。')+'</p>';
 basket();
}
function renderCoupons(){
 const coupons=state.coupons;
 $("coupons").className='coupons-stack';
 $("coupons").innerHTML=coupons.length?coupons.map(c=>`<button class="coupon-ticket ${state.coupon===c.id?'selected':''}" data-coupon="${esc(c.id)}" aria-pressed="${state.coupon===c.id}" ${state.mode==='demo'?'aria-disabled="true"':''}><span class="ticket-stamp">${state.mode==='demo'?'案例用券':'门店可用券'}</span><span><h4>${esc(c.title)}</h4><p>${state.mode==='demo'?'历史记录，不代表你当前持有此券':'选中后试算，不会核销或创建订单'}</p></span><span class="coupon-check">${state.coupon===c.id?'✓':''}</span></button>`).join(''):'<div class="coupon-empty">'+(state.mode==='demo'?'本案例没有可用于报价的券。':!state.store?'选好门店后，查看你在这家店可用的券。':'本次未返回可用券，仍可计算普通购买价格。')+'</div>';
}
function demoItems(){
 state.customDemo=null;
 $("store-caption").textContent=state.case==='extra'?'模拟案例 · 非真实优惠':'世界城广场餐厅 · 到店自取';
 const extra=state.case==='extra';
 state.products=extra?[{id:'demo-burger',name:'汉堡（模拟）',price:''},{id:'demo-drink',name:'饮品（模拟）',price:''}]:[{id:'1450',name:'麦香鸡',price:'16.50'},{id:state.case==='none'?'3505':'507411',name:state.case==='none'?'锡兰红茶':'中杯冰美式',price:state.case==='none'?'11.00':'11.90'}];
 if(state.case==='none')state.products=[{id:'case-tea',name:'麦香鸡＋锡兰红茶',price:''},{id:'case-coffee',name:'麦香鸡＋中杯冰美式',price:''}];
 state.selected=state.products.map(p=>p.id);state.coupons=state.case==='none'?[]:[{id:'demo',title:extra?'需加购配餐才可使用的券（模拟）':'9.9元中杯冰美式'}];state.coupon=state.coupons.length?'demo':'';
 renderMenu();renderCoupons();
}
function resultView(data){
 state.lastResult=data;
 const rows=data.result.results;
 if(!rows.length){$("result-content").innerHTML='<p class="menu-empty">本次没有成功报价。</p>';$("result").hidden=false;return;}
 const direct=rows[0],last=rows[rows.length-1];
 const saving=last.same_basket_saving_fen??last.saving_fen;
 const hasComparison=rows.length>1&&saving!==null&&saving!==undefined;
 const isExtra=saving!==null&&saving<0;
 const metric=(label,value,note)=>`<div class="metric"><span class="metric-label">${esc(label)}</span><div class="metric-value">${esc(value)}</div><span class="metric-note">${esc(note)}</span></div>`;
 let metrics='',verdict='';
 if(hasComparison){
  metrics=metric('不用券，实际付款',yuan(direct.payable_fen),'已计入当时原有促销')+metric('用券后，实际付款',yuan(last.payable_fen),last.within_budget?'在你的预算内':`超出预算 ${yuan(last.over_budget_fen)}`)+metric(isExtra?'实际多花':'实际少付',yuan(Math.abs(saving)),isExtra?'优惠不等于少花钱':(last.extra_items.length?'含额外餐品，请确认需要':'同样的餐，没有加购'));
  if(isExtra)verdict=`不用券付${yuan(direct.payable_fen)}，用券后反而付${yuan(last.payable_fen)}，多花${yuan(-saving)}。${last.extra_items.length?'还多买了：'+last.extra_items.join('、')+'。':''}如果本来不需要，就没必要为了用券加购。`;
  else verdict=`这张券让你实际少付${yuan(saving)}。${last.within_budget?'用券后在预算内。':`不过用券后仍比${yuan(data.budget_fen)}预算多${yuan(last.over_budget_fen)}，要不要买，由你决定。`}`;
 }else{
  metrics=metric(rows.length>1?'方案一':'不用券，实际付款',yuan(direct.payable_fen),direct.within_budget?'预算内':`超出 ${yuan(direct.over_budget_fen)}`)+metric(rows.length>1?'方案二':'你的预算',rows.length>1?yuan(last.payable_fen):yuan(data.budget_fen),rows.length>1?(last.within_budget?'预算内':`超出 ${yuan(last.over_budget_fen)}`):'不会替你调整预算')+metric('预算内可选',String(data.result.lowest_verified_options.length),'只统计已确认符合要求的方案');
  verdict=data.result.status==='options_found'?'这次有符合预算的方案。没有核验到用券报价，不宣称用券能省多少钱。':'本次查询还没找到符合全部要求、且在预算内的方案。保留你的预算，不强行凑单。';
 }
 if(data.mode==='live'&&data.report&&data.report.need){verdict+=' 本次只核对你选择的具体餐品与默认规格。';}
 const notes=rows.map(q=>{const descriptions=q.reasons.filter(r=>r!=='超预算').map(r=>r==='需求属性待确认'?(data.report.pending_question||'餐品要求待确认'):r);return `<li>${esc(q.name)}：${yuan(q.payable_fen)}${descriptions.length?'；'+esc(descriptions.join('；')):''}</li>`;}).join('');
 $("result-source").textContent=data.mode==='live'?'本轮真实查询':state.case==='extra'?'模拟案例 · 非真实优惠':'历史真实报价';
 $("result-content").innerHTML=`<div class="result-overview">${metrics}</div><div class="verdict"><span class="verdict-icon">${isExtra?'!':'✓'}</span><p>${esc(verdict)}</p></div><p class="result-meta">${esc(data.report.queried_at||'模拟数据，无真实查询时间')} · ${esc(data.report.store_label||'虚构门店')} · 仅比较本次候选</p><details class="comparison-details"><summary>展开餐品明细与数据来源</summary><ul>${notes}</ul><p>${esc(data.result.data_source)}</p><p>${esc(data.report.evidence||'见项目示例说明')}</p></details>`;
 if(rows.some(q=>!q.within_budget)){
  $("result-content").insertAdjacentHTML('beforeend','<div class="helper-actions"><button data-help="main">保留主食，看看别的饮品</button><button data-help="drink">保留饮品，换个主食</button></div>');
 }
 $("result").hidden=false;
 buddyEvent('result',data);
}
async function runDemo(){
 if(!$("budget").value.trim()||!Number.isFinite(Number($("budget").value))||Number($("budget").value)<0){message('请输入有效预算');return;}
 const rev=state.rev;try{const d=state.customDemo?repriceDemo(state.customDemo,Number($("budget").value)):await api('/api/demo?case='+encodeURIComponent(state.case)+'&budget='+encodeURIComponent($("budget").value));if(rev!==state.rev||state.mode!=='demo')return;resultView(d);message('');}catch(e){if(rev===state.rev)message(e.message);}
}
function setMode(mode){
 if(state.busy)return;state.mode=mode;state.mission='';document.querySelectorAll('[data-mission]').forEach(b=>b.classList.remove('active'));stale();message('');
 $("demo-mode").classList.toggle('active',mode==='demo');$("live-mode").classList.toggle('active',mode==='live');$("demo-mode").setAttribute('aria-pressed',String(mode==='demo'));$("live-mode").setAttribute('aria-pressed',String(mode==='live'));
 $("case-tabs").hidden=mode!=='demo';$("live-panel").hidden=mode!=='live';$("menu-controls").hidden=mode!=='live';$("source-badge").textContent=mode==='demo'?'历史实测':'你的实时查询';
 $("workspace-title").textContent=mode==='demo'?'先拿这份餐，算一笔账':'选好门店，看看你的券值不值';
 $("mode-description").textContent=mode==='demo'?'历史实测回放 · 无需登录 · 不消耗模型积分':'连接麦当劳官方 MCP · 无需模型会员 · 不下单';
 $("basket-note").textContent=mode==='demo'?'历史报价回放，餐品组合固定；预算可以调整。':'单品默认规格，每种1份。最终以价格试算结果为准。';
 $("menu-search").value='';state.category='全部';state.customDemo=null;$("plan-anchor").value='';
 buddyEvent(mode==='live'?'live':'hello');
 if(mode==='demo'){demoItems();runDemo();}else{
  state.products=[];state.coupons=[];state.selected=[];state.coupon='';state.store=null;$("stores").innerHTML='';$("categories").innerHTML='';$("store-caption").textContent='选择门店后显示菜单';
  $("connection-note").textContent=state.configured?'已提供本机连接配置。选择门店后查询；凭证不会发送到页面。':'尚未提供连接配置。关闭服务后，设置 MCD_MCP_TOKEN 或使用 --config 参数重新启动。现在仍可切回演示模式体验。';
  $("store-search").querySelector('button').disabled=!state.configured;renderMenu();renderCoupons();
 }
}
$("demo-mode").addEventListener('click',()=>setMode('demo'));$("live-mode").addEventListener('click',()=>setMode('live'));
$("case-tabs").addEventListener('click',e=>{const b=e.target.closest('[data-case]');if(!b||state.busy)return;state.case=b.dataset.case;stale();document.querySelectorAll('[data-case]').forEach(x=>x.classList.toggle('active',x===b));$("source-badge").textContent=state.case==='extra'?'模拟演示':'历史实测';demoItems();runDemo();});
$("budget").addEventListener('input',()=>{stale();buddyEvent('budget');});
$("menu").addEventListener('click',e=>{const b=e.target.closest('[data-product]');if(!b||state.busy)return;if(state.mode==='demo'){message('演示使用已核验的固定组合。要选择其他餐品，请切换“查我的门店与券”。');buddyEvent('demo-lock');return;}const id=b.dataset.product;if(state.selected.includes(id))state.selected=state.selected.filter(x=>x!==id);else{if(state.selected.length>=5){message('第一版最多比较5种单品，每种1份。');buddyEvent('limit');return;}state.selected.push(id);}stale();message('');renderMenu();buddyEvent(state.selected.length?'select':'empty');});
$("basket-items").addEventListener('click',e=>{const b=e.target.closest('[data-remove]');if(!b||state.busy)return;state.selected=state.selected.filter(x=>x!==b.dataset.remove);stale();renderMenu();buddyEvent(state.selected.length?'select':'empty');});
$("coupons").addEventListener('click',e=>{const b=e.target.closest('[data-coupon]');if(!b||state.mode==='demo'||state.busy)return;state.coupon=state.coupon===b.dataset.coupon?'':b.dataset.coupon;stale();renderCoupons();buddyEvent('coupon');});
$("menu-search").addEventListener('input',renderMenu);
$("categories").addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(!b)return;state.category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>x.classList.toggle('active',x===b));renderMenu();});
$("store-search").addEventListener('submit',async e=>{e.preventDefault();if(state.busy)return;const button=e.target.querySelector('button');button.disabled=true;state.busy=true;stale();message('正在查询附近门店…',true);try{const d=await api('/api/stores',{city:$("city").value,keyword:$("keyword").value});$("stores").innerHTML=d.stores.length?d.stores.map(s=>`<button class="store-option" data-store="${esc(s.id)}" data-name="${esc(s.name)}">${esc(s.name)}<small>${esc(s.hours)}${s.open===false?' · 当前未营业':''}</small></button>`).join(''):'<p class="menu-empty">没有找到门店，换一个关键词试试。</p>';message('');}catch(err){message(err.message);}finally{button.disabled=false;state.busy=false;basket();}});
$("stores").addEventListener('click',async e=>{const b=e.target.closest('[data-store]');if(!b||state.busy)return;state.busy=true;stale();state.store=null;state.products=[];state.selected=[];state.coupons=[];state.coupon='';renderMenu();renderCoupons();message('正在读取这家门店的菜单和可用券…',true);try{const d=await api('/api/menu',{store:b.dataset.store});state.store=d.store;state.products=d.products;state.coupons=d.coupons;$("store-caption").textContent=d.store.name+' · 到店自取';document.querySelectorAll('[data-store]').forEach(x=>x.classList.toggle('active',x===b));const categories=['全部',...new Set(d.products.map(p=>p.category))];$("categories").innerHTML=categories.map(c=>`<button data-category="${esc(c)}" class="${c==='全部'?'active':''}">${esc(c)}</button>`).join('');state.category='全部';message('');renderMenu();renderCoupons();}catch(err){message(err.message);}finally{state.busy=false;basket();}});
$("compare").addEventListener('click',async()=>{if(state.busy)return;if(state.mode==='demo'){await runDemo();return;}state.busy=true;stale();const rev=state.rev;basket();$("compare").innerHTML='<span class="busy-indicator"></span>正在分别核验报价…';message('正在核验餐品与用券前后应付金额，不会创建订单。',true);try{const d=await api('/api/compare',{store:state.store?.id,products:state.selected,coupon:state.coupon,budget:$("budget").value});if(rev!==state.rev)return;resultView(d);message('');$("result").scrollIntoView({behavior:'smooth',block:'start'});}catch(e){message(e.message);}finally{state.busy=false;$("compare").innerHTML='算算实际少付多少 <span>→</span>';basket();}});

function refreshPlanner(){
 const select=$("plan-anchor"),current=select.value;
 const candidates=state.mode==='demo'?[{id:'1450',name:'麦香鸡'},{id:'507411',name:'中杯冰美式'},{id:'3505',name:'锡兰红茶'}]:selectedItems();
 if(current&&!candidates.some(p=>p.id===current)){const retained=state.products.find(p=>p.id===current);if(retained)candidates.push(retained);}
 select.innerHTML='<option value="">不用，帮我重新搭</option>'+candidates.map(p=>`<option value="${esc(p.id)}">保留${esc(p.name)}</option>`).join('');
 if(candidates.some(p=>p.id===current))select.value=current;
 $("find-meal").disabled=state.busy||(state.mode==='live'&&!state.store);
 $("plan-coupon").disabled=state.busy||!state.coupon;
 $("planner-source").textContent=state.mode==='demo'?'历史报价池':'本轮价格核验';
 $("planner-hint").textContent=state.mode==='demo'?'只筛选已有的两组历史报价；预算仍由你决定。':'主食＋饮品各1份，使用右侧预算；最多核验6组，价格以接口试算为准。';
}
async function findSuggestions(anchor,couponFocus=false){
 if(state.busy)return;
 if(anchor!==undefined)$("plan-anchor").value=anchor;
 const preserved=$("plan-anchor").value;const rev=++state.rev;state.busy=true;$("result").hidden=true;$("suggestion-panel").hidden=true;basket();
 const payload={store:state.store?.id,budget:$("budget").value,main:$("plan-main").value,drink:$("plan-drink").value,anchor:preserved,coupon:state.coupon,coupon_focus:couponFocus};
 const button=$("find-meal"),original=button.innerHTML;button.textContent='正在找搭配…';message(state.mode==='demo'?'正在筛选历史报价…':'正在逐组核验价格，最多6组，请稍等…',true);
 try{
  const data=await api(state.mode==='demo'?'/api/demo-suggest':'/api/suggest',payload);if(rev!==state.rev)return;
  state.suggestions=data.options;const within=data.options.filter(o=>o.within_budget).length;
  $("suggestion-summary").textContent=data.options.length?(within?`这次展示${data.options.length}组，其中${within}组在预算内。`:'这次核验的方案都超预算，先看看差多少，不替你加预算。'):'没有找到符合所选范围且成功报价的组合。可以更换偏好，预算保持不变。';
  $("suggestion-options").innerHTML=data.options.map((o,index)=>`<article class="suggestion-option"><span class="suggestion-status">${o.coupon_applied?'已核验用券价':'已核验不用券价'}${o.products.length===state.selected.length&&o.products.every(id=>state.selected.includes(id))?' · 当前组合':''}</span><h4>${o.names.map(esc).join(' ＋ ')}</h4><div class="suggestion-price">${yuan(o.payable_fen)}</div><p class="suggestion-budget">${o.within_budget?'在预算内':`超出预算 ${yuan(o.over_budget_fen)}`}</p>${preserved?'<p class="swap-note">保留了你指定的餐品，各1份</p>':''}<button data-use-plan="${index}">选这份，看详细对比</button><details><summary>报价时间</summary><p>${esc(o.queried_at)}</p></details></article>`).join('');
  $("suggestion-scope").textContent=`${data.mode==='demo'?'历史记录筛选':'本轮核验'} ${data.tested}组，成功${data.successful}组${data.failed?`，${data.failed}组因规格或报价问题跳过`:''}。${data.scope}`;
  $("suggestion-panel").hidden=false;message('');buddyEvent('suggestions',data);
 }catch(e){message(e.message);}finally{state.busy=false;button.innerHTML=original;basket();}
}
$("find-meal").addEventListener('click',()=>state.mission==='coupon'?$("plan-coupon").click():findSuggestions());
for(const id of ['plan-main','plan-drink','plan-anchor'])$(id).addEventListener('change',()=>{state.rev++;$("suggestion-panel").hidden=true;});
$("plan-coupon").addEventListener('click',()=>{
 if(state.busy)return;
 const coupon=state.coupons.find(c=>c.id===state.coupon);
 const products=state.mode==='demo'?[{id:'507411',name:'中杯冰美式'}]:(coupon?.products||[]).filter(p=>state.products.some(v=>v.id===p.id));
 if(!products.length){message('当前菜单中没有找到该券对应的餐品');return;}
 if(products.length>1){message('这张券对应多种餐品，请先选定其中一种，再使用“保留它，换另一种”。');return;}
 // A coupon product can be retained even if not yet added to the basket.
 const target=products[0];const select=$("plan-anchor");
 if(!Array.from(select.options).some(o=>o.value===target.id))select.add(new Option('保留'+target.name,target.id));
 select.value=target.id;findSuggestions(undefined,true);
});
$("suggestion-options").addEventListener('click',e=>{
 const b=e.target.closest('[data-use-plan]');if(!b||state.busy)return;
 const option=state.suggestions[Number(b.dataset.usePlan)];if(!option)return;
 stale();state.coupon=option.coupon;state.selected=option.products.slice();
 if(state.mode==='demo'){
  state.customDemo=option.comparison;state.products=option.products.map((id,i)=>({id,name:option.names[i],price:''}));
  state.coupons=option.coupon?[{id:'demo',title:'9.9元中杯冰美式'}]:[];
 }
 renderMenu();renderCoupons();resultView(option.comparison);message('');
 buddyEvent('result',option.comparison);$("result").scrollIntoView({behavior:'smooth',block:'start'});
});
$("basket-items").addEventListener('click',e=>{const b=e.target.closest('[data-keep]');if(b&&!state.busy)findSuggestions(b.dataset.keep);});
$("result-content").addEventListener('click',e=>{
 const b=e.target.closest('[data-help]');if(!b||state.busy)return;
 const product=selectedItems().find(p=>b.dataset.help==='main'?/堡|卷|麦满分/.test(p.name):/咖|茶|美式|拿铁|可乐|雪碧|纯悦|水/.test(p.name));
 if(product)findSuggestions(product.id);else message('请在“这次想保留”中选一种餐品，再找搭配。');
});

const savedKey='mcd-saved-meals-v1';
let savedMeals=[];
try{const raw=JSON.parse(localStorage.getItem(savedKey)||'[]');if(Array.isArray(raw))savedMeals=raw.slice(0,8).map(MealTools.favorite);}catch{}
function renderSaved(){
 $("saved-count").textContent=`${savedMeals.length}份`;
 $("saved-list").innerHTML=savedMeals.length?savedMeals.map((meal,i)=>`<article class="saved-card"><div><b>${meal.products.map(p=>esc(p.name)).join(' ＋ ')}</b><small>${meal.mode==='demo'?'案例搭配':esc(meal.store.name)} · 保存预算 ¥${esc(meal.budget)}</small></div><button data-restore="${i}">恢复并重新算价</button><button data-delete="${i}" aria-label="删除这份收藏">×</button></article>`).join(''):'<p class="saved-empty">把常吃的存下来，下次少翻一遍菜单。</p>';
}
function writeSaved(next){try{localStorage.setItem(savedKey,JSON.stringify(next));savedMeals=next;renderSaved();return true;}catch{$("saved-status").textContent='浏览器不允许本地保存，这次没有写入。';return false;}}
$("save-meal").addEventListener('click',()=>{
 if(state.busy)return;
 try{
  if(state.mode==='demo'&&state.case==='none')throw Error('这是多个方案的比较，请先选定一份搭配再收藏。');
  const meal=MealTools.favorite({mode:state.mode,case:state.case,products:selectedItems(),store:state.store,budget:$("budget").value});
  const signature=m=>JSON.stringify([m.mode,m.store?.id,m.case,m.products.map(p=>p.id).sort()]);
  const next=[meal,...savedMeals.filter(m=>signature(m)!==signature(meal))].slice(0,8);
  if(writeSaved(next)){$("save-status").textContent='已收藏 · 下次恢复会重新算价';buddyEvent('saved');}
 }catch(e){$("save-status").textContent=e.message;}
});
$("saved-list").addEventListener('click',async e=>{
 const remove=e.target.closest('[data-delete]');if(remove){writeSaved(savedMeals.filter((_,i)=>i!==Number(remove.dataset.delete)));return;}
 const b=e.target.closest('[data-restore]');if(!b||state.busy)return;
 const meal=savedMeals[Number(b.dataset.restore)];if(!meal)return;
 if(meal.mode==='live'&&(state.mode!=='live'||state.store?.id!==meal.store.id)){
  $("saved-status").textContent=`先在实时模式搜索并选中“${meal.store.name}”，然后再点恢复；不会跨门店套用餐品或旧券。`;
  if(state.mode!=='live')setMode('live');$("keyword").value=meal.store.name;return;
 }
 if(meal.mode==='live'){
  if(meal.products.some(p=>!state.products.some(v=>v.id===p.id))){$("saved-status").textContent='这家店当前菜单未包含收藏中的全部餐品，请重新选餐。';return;}
  stale();$("budget").value=meal.budget;state.selected=meal.products.map(p=>p.id);state.coupon='';renderMenu();renderCoupons();
  $("saved-status").textContent='餐品与保存预算已恢复，未恢复旧券。请选择当前券，再点“算算实际少付多少”。';buddyEvent('select');return;
 }
 if(state.mode!=='demo')setMode('demo');
 state.case=meal.case;stale();$("budget").value=meal.budget;demoItems();
 document.querySelectorAll('[data-case]').forEach(x=>x.classList.toggle('active',x.dataset.case===state.case));
 $("source-badge").textContent=state.case==='extra'?'模拟演示':'历史实测';
 if(meal.products.some(p=>p.id==='3505')){
  const rev=state.rev;try{
   const data=await api('/api/demo-suggest',{budget:meal.budget,drink:'tea',main:'chicken',coupon:'',anchor:''});
   if(rev!==state.rev||state.mode!=='demo')return;
   const option=data.options[0];if(!option)throw Error('这份历史记录当前不可用');
   state.customDemo=option.comparison;state.selected=option.products;state.products=option.products.map((id,i)=>({id,name:option.names[i],price:''}));state.coupons=[];state.coupon='';renderMenu();renderCoupons();resultView(option.comparison);
  }catch(err){$("saved-status").textContent=err.message;return;}
 }else await runDemo();
 $("saved-status").textContent='已恢复保存的预算和案例；这是历史或模拟数据，不代表当前价格。';
});
document.querySelectorAll('[data-mission]').forEach(button=>button.addEventListener('click',()=>{
 if(state.busy)return;
 const mission=button.dataset.mission;
 if(mission==='coupon'&&!state.coupon){$("mission-note").textContent='先在下方选择一张当前可用券。没有券，也可以正常比较普通价格。';return;}
 state.mission=mission;$("plan-anchor").value='';$("plan-main").value='chicken';$("plan-drink").value=mission==='coupon'?'any':mission;
 stale();document.querySelectorAll('[data-mission]').forEach(b=>b.classList.toggle('active',b===button));
 $("mission-note").textContent=mission==='coupon'?'会比较只买券餐品与搭配方案；点“按预算找搭配”开始，不替你增加预算。':`已选${mission==='coffee'?'主食＋咖啡':'主食＋茶饮'}。点“按预算找搭配”开始，保留你的现有预算。`;
 buddyEvent('mission');
}));
for(const id of ['plan-main','plan-drink','plan-anchor'])$(id).addEventListener('change',()=>{state.mission='';document.querySelectorAll('[data-mission]').forEach(b=>b.classList.remove('active'));});
$("export-receipt").addEventListener('click',()=>{
 if(!state.lastResult){message('餐品或预算已变动，请先重新算价再导出。');return;}
 try{
  const html=MealTools.receipt(state.lastResult),url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download='麦乐省钱侠-比价小票.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
 }catch(e){message(e.message);}
});
renderSaved();

(async()=>{try{const d=await api('/api/status');state.csrf=d.csrf;state.configured=d.configured;}catch(e){message('无法连接本地服务，请通过 python app.py ui 启动。');}demoItems();await runDemo();})();
