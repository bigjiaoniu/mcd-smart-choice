const test=require('node:test');
const assert=require('node:assert/strict');
const {favorite,receipt}=require('../web/meal-tools.js');
const sample=()=>({mode:'demo',case:'coupon',budget_fen:2500,report:{queried_at:'2026-10-17',store_label:'历史门店',evidence:'历史证据'},result:{results:[{name:'不用券',payable_fen:2840,within_budget:false,over_budget_fen:340},{name:'用券',payable_fen:2640,same_basket_saving_fen:200,within_budget:false,over_budget_fen:140}]}});
test('收藏仅保存白名单，不保留凭证、券或旧报价',()=>{
 const meal=favorite({mode:'live',budget:'25',store:{id:'123',name:'门店',token:'SECRET'},products:[{id:'1450',name:'麦香鸡',price:'16.5'}],couponCode:'PRIVATE',result:sample()});
 assert.deepEqual(meal.products,[{id:'1450',name:'麦香鸡'}]);assert.deepEqual(meal.store,{id:'123',name:'门店'});assert.ok(!JSON.stringify(meal).includes('PRIVATE'));assert.equal(meal.result,undefined);
});
test('拒绝无效预算、空餐品、超上限餐品',()=>{
 const base={mode:'demo',budget:'25',products:[{id:'1',name:'餐品'}]};
 for(const budget of ['-1','NaN','25.001',''])assert.throws(()=>favorite({...base,budget}));
 assert.throws(()=>favorite({...base,products:[]}));assert.throws(()=>favorite({...base,products:Array(6).fill(base.products[0])}));
});
test('小票明确历史来源、额外省2元和超预算1.40元',()=>{
 const result=receipt(sample());assert.ok(result.includes('历史报价回放'));assert.ok(result.includes('少付 ¥2.00'));assert.ok(result.includes('超 ¥1.40'));assert.ok(!result.includes('<script'));
});
test('模拟小票不伪装真实，动态文字转义且不输出完整数据',()=>{
 const data=sample();data.case='extra';data.report.store_label='<script>alert(1)</script>';data.report.token='SECRET';data.couponCode='PRIVATE';
 const result=receipt(data);assert.ok(result.includes('模拟案例'));assert.ok(result.includes('&lt;script&gt;'));assert.ok(!result.includes('<script>'));assert.ok(!result.includes('SECRET'));assert.ok(!result.includes('PRIVATE'));
});
test('用券多花显示额外餐品和支出，无可比较价格不宣称节省',()=>{
 const data=sample();data.result.results[1].same_basket_saving_fen=null;data.result.results[1].saving_fen=-200;data.result.results[1].extra_items=['薯条'];
 assert.ok(receipt(data).includes('反而多花 ¥2.00'));assert.ok(receipt(data).includes('额外餐品：薯条'));
 data.result.results=data.result.results.slice(0,1);assert.ok(receipt(data).includes('不宣称用券省钱'));
});
