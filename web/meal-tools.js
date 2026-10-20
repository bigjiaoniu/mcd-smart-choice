/* Local-only saved meals and a shareable receipt. Never persist coupons or quotes. */
(function(root){
 const text=(v,max=160)=>String(v??'').slice(0,max);
 const escape=(v)=>text(v,4000).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const money=v=>{if(!Number.isSafeInteger(v)||v<0)throw Error('报价金额无效');return `¥${(v/100).toFixed(2)}`;};
 function favorite(raw){
  if(!raw||!['live','demo'].includes(raw.mode)||!Array.isArray(raw.products)||!raw.products.length||raw.products.length>5)throw Error('请先选择餐品');
  const budget=String(raw.budget??'');if(!/^\d+(\.\d{1,2})?$/.test(budget)||!Number.isSafeInteger(Math.round(Number(budget)*100)))throw Error('请输入有效预算，最多两位小数');
  const products=raw.products.map(p=>{if(!/^[\w-]{1,80}$/.test(p.id)||!p.name)throw Error('餐品记录无效');return {id:p.id,name:text(p.name,100)};});
  const store=raw.mode==='live'?{id:text(raw.store?.id,40),name:text(raw.store?.name,100)}:null;
  if(raw.mode==='live'&&(!/^\d+$/.test(store.id)||!store.name))throw Error('请先选择门店');
  return {mode:raw.mode,case:['coupon','extra'].includes(raw.case)?raw.case:'coupon',budget,store,products};
 }
 function receipt(data){
  const rows=data?.result?.results;if(!rows?.length)throw Error('请先完成报价');
  const last=rows.at(-1),saving=last.same_basket_saving_fen??last.saving_fen;
  const source=data.mode==='live'?'本轮真实查询':data.case==='extra'?'模拟案例（非真实优惠）':'历史报价回放（非当前价格）';
  const budget=money(data.budget_fen);
  let summary='未取得可比较的优惠券增量节省，不宣称用券省钱。';
  if(rows.length>1&&Number.isSafeInteger(saving))summary=saving<0?`用券反而多花 ${money(-saving)}，别为了券加购。`:`用券实际少付 ${money(saving)}，已扣除不用券也能享受的优惠。`;
  const body=rows.map(r=>`<tr><td>${escape(r.name)}${r.extra_items?.length?`<small>额外餐品：${escape(r.extra_items.join('、'))}</small>`:''}${r.reasons?.length?`<small>${escape(r.reasons.join('；'))}</small>`:''}</td><td>${money(r.payable_fen)}</td><td>${r.within_budget?'预算内':`超 ${money(r.over_budget_fen)}`}</td></tr>`).join('');
  return `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>麦乐省钱侠的比价小票</title><style>body{background:#f8f6f1;color:#29251f;font:15px/1.8 system-ui,'Microsoft YaHei';padding:24px;margin:0}main{max-width:680px;margin:auto;background:#fffdf8;padding:28px;border-top:7px solid #cd1b23;border-radius:12px}h1{font-size:27px;margin:0}b{color:#b91e29}table{width:100%;border-collapse:collapse;margin:20px 0}td,th{text-align:left;padding:12px 6px;border-bottom:1px dashed #ded4c1}td:not(:first-child){white-space:nowrap}small{display:block;color:#857962;font-size:11px}.source{display:inline-block;background:#fff0bd;padding:3px 10px;border-radius:4px;font-size:12px}footer{border-top:1px solid #e8deca;margin-top:24px;padding-top:12px;color:#8c7d65;font-size:11px}p{overflow-wrap:anywhere}@media(max-width:480px){body{padding:10px}main{padding:18px}table{font-size:11px}td,th{padding:9px 3px}h1{font-size:22px}}@media print{body{padding:0;background:white}main{border:0}}</style><main><p class="source">${source}</p><h1>这顿饭，算明白了。</h1><p>麦乐省钱侠 · 麦麦明白点<br>预算 <b>${budget}</b> · ${escape(data.report?.store_label||'见案例说明')}</p><table><thead><tr><th>已核验的买法</th><th>实际应付</th><th>预算</th></tr></thead><tbody>${body}</tbody></table><p><b>${summary}</b></p><p>查询时间：${escape(data.report?.queried_at||'模拟数据，无真实查询时间')}<br>证据：${escape(data.report?.evidence||data.result.data_source||'见项目案例说明')}</p><footer>仅比较本次候选，不保证最低价。历史与模拟记录不代表现在可购买；价格仅适用于记录中的门店、账号与时点。非官方产品；未下单、未支付。<br>github.com/bigjiaoniu/mcd-smart-choice</footer></main></html>`;
 }
 root.MealTools={favorite,receipt};
 if(typeof module!=='undefined'&&module.exports)module.exports={favorite,receipt};
})(typeof globalThis!=='undefined'?globalThis:this);
