"use strict";
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const yuan = (v) => `¥${(v / 100).toFixed(2)}`;
const state = {mode:"demo",case:"coupon",csrf:"",configured:false,products:[],coupons:[],selected:[],coupon:"",store:null,category:"全部",rev:0,busy:false};
const icon = (name) => {
 const coffee = /咖|茶|饮|水|可乐|雪碧|美式|拿铁|奶铁/.test(name);
 return coffee ? '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M16 18h32l-4 38H21z" fill="#f3e7d0"/><path d="M19 27h26l-2 17H21z" fill="#75422b"/><path d="M13 16h38v5H13z" fill="#c79150"/><path d="M32 17l5-13h4l-5 13z" fill="#bc4d32"/><path d="M22 27l7 6 6-7 6 6" fill="none" stroke="#b78d63" stroke-width="4"/></svg>' : '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M8 28c1-13 10-21 24-21s24 8 24 21" fill="#eab34d"/><path d="M9 29h46l-4 8H13z" fill="#79a047"/><path d="M9 37h46v8H9z" fill="#81412c"/><path d="M10 44h44l-6 6H16z" fill="#f0ba37"/><path d="M10 51h44c-2 7-10 9-22 9s-20-2-22-9" fill="#dfa244"/><g stroke="#fff0c7" stroke-width="2" stroke-linecap="round"><path d="M22 17l3-1M35 14l3 1M43 22l3 1M29 24l3-1"/></g></svg>';
};
function message(msg, busy=false){$("message").hidden=!msg;$("message").innerHTML=busy ? `<span class="busy-indicator"></span>${esc(msg)}` : esc(msg);}
function stale(){state.rev++;$("result").hidden=true;}
async function api(path, body){
 if(window.__OFFLINE_DEMOS){
  if(path==='/api/status')return {configured:false,csrf:''};
  if(path.startsWith('/api/demo?')){
   const params=new URLSearchParams(path.split('?')[1]);const rawBudget=params.get('budget')||'';const budget=Number(rawBudget);
   if(!rawBudget.trim()||!Number.isFinite(budget)||budget<0||Math.abs(budget*100-Math.round(budget*100))>0.000001)throw Error('请输入有效预算，最多两位小数');
   const doc=structuredClone(window.__OFFLINE_DEMOS[params.get('case')||'coupon']);doc.budget_fen=Math.round(budget*100);
   for(const q of doc.result.results){q.within_budget=q.payable_fen<=doc.budget_fen;q.over_budget_fen=Math.max(0,q.payable_fen-doc.budget_fen);q.reasons=q.reasons.filter(r=>r!=='超预算');if(!q.within_budget)q.reasons.push('超预算');}
   const eligible=doc.result.results.filter(q=>q.qualified&&q.within_budget);const min=Math.min(...eligible.map(q=>q.payable_fen));
   doc.result.lowest_verified_options=eligible.filter(q=>q.payable_fen===min).map(q=>q.name);doc.result.status=eligible.length?'options_found':'no_eligible_option';return doc;
  }
  throw Error('这是离线预览，实时查询请启动本地可视化版本。');
 }
 const options=body?{method:"POST",headers:{"Content-Type":"application/json","X-Local-CSRF":state.csrf},body:JSON.stringify(body)}:{};
 const r=await fetch(path, options);const d=await r.json();if(!r.ok)throw Error(d.error||"请求未完成，请重试");return d;
}
function selectedItems(){return state.products.filter(p=>state.selected.includes(p.id));}
function basket(){
 const items=selectedItems();const alternatives=state.mode==='demo'&&state.case==='none';
 $("basket-count").textContent=`${items.length}${alternatives?'组':'件'}`;
 document.querySelector('.basket-heading h3').textContent=alternatives?'本次比较的方案':'我的这份餐';
 $("basket-items").innerHTML=items.length?items.map(p=>`<div class="basket-line"><span>${esc(p.name)}</span><span>× 1 ${state.mode==='live'?`<button class="basket-remove" data-remove="${esc(p.id)}" aria-label="移除${esc(p.name)}">×</button>`:''}</span></div>`).join(''):'<p class="menu-empty">从左侧选择想吃的单品。</p>';
 $("compare").disabled=state.busy||(state.mode==='live'&&!items.length);
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
 $("store-caption").textContent=state.case==='extra'?'模拟案例 · 非真实优惠':'世界城广场餐厅 · 到店自取';
 const extra=state.case==='extra';
 state.products=extra?[{id:'demo-burger',name:'汉堡（模拟）',price:''},{id:'demo-drink',name:'饮品（模拟）',price:''}]:[{id:'1450',name:'麦香鸡',price:'16.50'},{id:state.case==='none'?'3505':'507411',name:state.case==='none'?'锡兰红茶':'中杯冰美式',price:state.case==='none'?'11.00':'11.90'}];
 if(state.case==='none')state.products=[{id:'case-tea',name:'麦香鸡＋锡兰红茶',price:''},{id:'case-coffee',name:'麦香鸡＋中杯冰美式',price:''}];
 state.selected=state.products.map(p=>p.id);state.coupons=state.case==='none'?[]:[{id:'demo',title:extra?'需加购配餐才可使用的券（模拟）':'9.9元中杯冰美式'}];state.coupon=state.coupons.length?'demo':'';
 renderMenu();renderCoupons();
}
function resultView(data){
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
 $("result").hidden=false;
}
async function runDemo(){
 const rev=state.rev;try{const d=await api('/api/demo?case='+encodeURIComponent(state.case)+'&budget='+encodeURIComponent($("budget").value));if(rev!==state.rev||state.mode!=='demo')return;resultView(d);message('');}catch(e){if(rev===state.rev)message(e.message);}
}
function setMode(mode){
 if(state.busy)return;state.mode=mode;stale();message('');
 $("demo-mode").classList.toggle('active',mode==='demo');$("live-mode").classList.toggle('active',mode==='live');$("demo-mode").setAttribute('aria-pressed',String(mode==='demo'));$("live-mode").setAttribute('aria-pressed',String(mode==='live'));
 $("case-tabs").hidden=mode!=='demo';$("live-panel").hidden=mode!=='live';$("menu-controls").hidden=mode!=='live';$("source-badge").textContent=mode==='demo'?'历史实测':'你的实时查询';
 $("workspace-title").textContent=mode==='demo'?'先拿这份餐，算一笔账':'选好门店，看看你的券值不值';
 $("mode-description").textContent=mode==='demo'?'历史实测回放 · 无需登录 · 不消耗模型积分':'连接麦当劳官方 MCP · 无需模型会员 · 不下单';
 $("basket-note").textContent=mode==='demo'?'历史报价回放，餐品组合固定；预算可以调整。':'单品默认规格，每种1份。最终以价格试算结果为准。';
 $("menu-search").value='';state.category='全部';
 if(mode==='demo'){demoItems();runDemo();}else{
  state.products=[];state.coupons=[];state.selected=[];state.coupon='';state.store=null;$("stores").innerHTML='';$("categories").innerHTML='';$("store-caption").textContent='选择门店后显示菜单';
  $("connection-note").textContent=state.configured?'已提供本机连接配置。选择门店后查询；凭证不会发送到页面。':'尚未提供连接配置。关闭服务后，设置 MCD_MCP_TOKEN 或使用 --config 参数重新启动。现在仍可切回演示模式体验。';
  $("store-search").querySelector('button').disabled=!state.configured;renderMenu();renderCoupons();
 }
}
$("demo-mode").addEventListener('click',()=>setMode('demo'));$("live-mode").addEventListener('click',()=>setMode('live'));
$("case-tabs").addEventListener('click',e=>{const b=e.target.closest('[data-case]');if(!b||state.busy)return;state.case=b.dataset.case;stale();document.querySelectorAll('[data-case]').forEach(x=>x.classList.toggle('active',x===b));$("source-badge").textContent=state.case==='extra'?'模拟演示':'历史实测';demoItems();runDemo();});
$("budget").addEventListener('input',()=>stale());
$("menu").addEventListener('click',e=>{const b=e.target.closest('[data-product]');if(!b||state.busy)return;if(state.mode==='demo'){message('演示使用已核验的固定组合。要选择其他餐品，请切换“查我的门店与券”。');return;}const id=b.dataset.product;if(state.selected.includes(id))state.selected=state.selected.filter(x=>x!==id);else{if(state.selected.length>=5){message('第一版最多比较5种单品，每种1份。');return;}state.selected.push(id);}stale();message('');renderMenu();});
$("basket-items").addEventListener('click',e=>{const b=e.target.closest('[data-remove]');if(!b||state.busy)return;state.selected=state.selected.filter(x=>x!==b.dataset.remove);stale();renderMenu();});
$("coupons").addEventListener('click',e=>{const b=e.target.closest('[data-coupon]');if(!b||state.mode==='demo'||state.busy)return;state.coupon=state.coupon===b.dataset.coupon?'':b.dataset.coupon;stale();renderCoupons();});
$("menu-search").addEventListener('input',renderMenu);
$("categories").addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(!b)return;state.category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>x.classList.toggle('active',x===b));renderMenu();});
$("store-search").addEventListener('submit',async e=>{e.preventDefault();if(state.busy)return;const button=e.target.querySelector('button');button.disabled=true;state.busy=true;stale();message('正在查询附近门店…',true);try{const d=await api('/api/stores',{city:$("city").value,keyword:$("keyword").value});$("stores").innerHTML=d.stores.length?d.stores.map(s=>`<button class="store-option" data-store="${esc(s.id)}" data-name="${esc(s.name)}">${esc(s.name)}<small>${esc(s.hours)}${s.open===false?' · 当前未营业':''}</small></button>`).join(''):'<p class="menu-empty">没有找到门店，换一个关键词试试。</p>';message('');}catch(err){message(err.message);}finally{button.disabled=false;state.busy=false;basket();}});
$("stores").addEventListener('click',async e=>{const b=e.target.closest('[data-store]');if(!b||state.busy)return;state.busy=true;stale();state.store=null;state.products=[];state.selected=[];state.coupons=[];state.coupon='';renderMenu();renderCoupons();message('正在读取这家门店的菜单和可用券…',true);try{const d=await api('/api/menu',{store:b.dataset.store});state.store=d.store;state.products=d.products;state.coupons=d.coupons;$("store-caption").textContent=d.store.name+' · 到店自取';document.querySelectorAll('[data-store]').forEach(x=>x.classList.toggle('active',x===b));const categories=['全部',...new Set(d.products.map(p=>p.category))];$("categories").innerHTML=categories.map(c=>`<button data-category="${esc(c)}" class="${c==='全部'?'active':''}">${esc(c)}</button>`).join('');state.category='全部';message('');renderMenu();renderCoupons();}catch(err){message(err.message);}finally{state.busy=false;basket();}});
$("compare").addEventListener('click',async()=>{if(state.busy)return;if(state.mode==='demo'){await runDemo();return;}state.busy=true;stale();const rev=state.rev;basket();$("compare").innerHTML='<span class="busy-indicator"></span>正在分别核验报价…';message('正在核验餐品与用券前后应付金额，不会创建订单。',true);try{const d=await api('/api/compare',{store:state.store?.id,products:state.selected,coupon:state.coupon,budget:$("budget").value});if(rev!==state.rev)return;resultView(d);message('');$("result").scrollIntoView({behavior:'smooth',block:'start'});}catch(e){message(e.message);}finally{state.busy=false;$("compare").innerHTML='算算实际少付多少 <span>→</span>';basket();}});
(async()=>{try{const d=await api('/api/status');state.csrf=d.csrf;state.configured=d.configured;}catch(e){message('无法连接本地服务，请通过 python app.py ui 启动。');}demoItems();await runDemo();})();
