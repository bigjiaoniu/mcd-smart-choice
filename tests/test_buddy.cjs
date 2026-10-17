const test=require('node:test');
const assert=require('node:assert/strict');
const {respond}=require('../web/buddy-rules.js');
const payload=(rows,status='no_eligible_option')=>({result:{results:rows,status}});
test('超预算台词引用本次差额，不虚构省钱',()=>{
 const reply=respond('result',payload([{within_budget:false,over_budget_fen:340},{within_budget:false,over_budget_fen:140,same_basket_saving_fen:200}]));
 assert.equal(reply.mood,'skeptical');assert.ok(reply.text.includes('¥1.40'));assert.ok(reply.text.includes('¥2.00'));
});
test('用券多花优先提醒加购，即使仍在预算内',()=>{
 const reply=respond('result',payload([{within_budget:true},{within_budget:true,saving_fen:-200}],'options_found'));
 assert.equal(reply.mood,'shocked');assert.ok(reply.text.includes('¥2.00'));assert.ok(reply.text.includes('多花'));
});
test('同款省钱且预算内才庆祝',()=>{
 const reply=respond('result',payload([{within_budget:false},{within_budget:true,same_basket_saving_fen:200}],'options_found'));
 assert.equal(reply.mood,'happy');assert.ok(reply.text.includes('¥2.00'));
});
test('没有报价不编造价格',()=>{
 const reply=respond('result',payload([]));assert.equal(reply.mood,'confused');assert.ok(!reply.text.includes('¥'));
});
test('空购物篮指导先选餐',()=>{assert.equal(respond('empty').mood,'confused');});
test('请求失败不伪装成省钱成功',()=>{const r=respond('error');assert.equal(r.mood,'confused');assert.ok(!r.text.includes('¥'));});
test('修改预算先要求重新计算',()=>{const r=respond('budget');assert.equal(r.mood,'thinking');assert.ok(!r.text.includes('¥'));});
test('相同事实可换台词但不改金额',()=>{
 const p=payload([{within_budget:false,over_budget_fen:140,same_basket_saving_fen:200}]);
 const a=respond('result',p,0),b=respond('result',p,1);assert.notEqual(a.text,b.text);assert.ok(a.text.includes('¥1.40'));assert.ok(b.text.includes('¥1.40'));
});

test('找到搭配时按实际展示结果计数',()=>{
 const r=respond('suggestions',{options:[{within_budget:true},{within_budget:false}]});
 assert.equal(r.mood,'happy');assert.ok(r.text.includes('1份'));
});
