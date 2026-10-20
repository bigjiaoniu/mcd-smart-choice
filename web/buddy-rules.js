/* Original budget companion. Deterministic local rules, no model or network calls. */
(function(root){
 const money=(fen)=>`¥${(fen/100).toFixed(2)}`;
 function respond(event,payload={},variant=0){
  let mood='idle',lines=[];
  if(event==='result'){
   const rows=payload.result?.results||[];const last=rows.at(-1);
   const saving=last?.same_basket_saving_fen??last?.saving_fen;
   if(Number.isInteger(saving)&&saving<0){mood='shocked';lines=[`券是用了，账单怎么还长高了？反而多花${money(-saving)}，先别急着夸它。`,`为了优惠多花${money(-saving)}？这张券有点会做生意哦。别为了用它，买本来不需要的东西。`];}
   else if(rows.length&&rows.every(q=>!q.within_budget)){
    mood='skeptical';const over=Math.min(...rows.map(q=>q.over_budget_fen));
    const prefix=Number.isInteger(saving)&&saving>0?`省了${money(saving)}是好事，`:'这几份都超预算了，';
    lines=[`${prefix}但这几份里最少还超${money(over)}。嘴巴说可以，钱包还没签字呢。`,`预算可不会因为有优惠券就自己长高。这次查到的方案至少超${money(over)}，要不要买，你说了算。`];
   }else if(Number.isInteger(saving)&&saving>0){mood='happy';lines=[`嗯哼，少付${money(saving)}，还在预算里！这次是钱包赢了一局。`,`同样的餐少花${money(saving)}，没有让优惠牵着走。今天的精打细算冠军，先给你。`];}
   else if(payload.result?.status==='no_eligible_option'){mood='confused';lines=['先等等，还有条件没确认。不能因为看着便宜，就假装它全都合适。','这次还没找到合适的。菜单那么大，也不差多看一眼嘛。'];}
   else{mood='smug';lines=['报价有了，用券省钱的证据还没齐。咱不替优惠券吹牛，先看实际付款。','嗯，这次先看普通买多少钱。没查到适用券，也不用硬凑一个。'];}
  }else if(event==='suggestions'){const count=(payload.options||[]).filter(o=>o.within_budget).length;mood=count?'happy':'thinking';lines=count?[`这次找到${count}份预算内的候选。先看看想不想吃，便宜可不是唯一标准哦。`]:['这几份还没进预算，我没偷偷给你加钱。换个偏好试试，别急着凑单。'];
  }else if(event==='saved'){mood='smug';lines=['这份搭配记在小本本了。下次恢复再查价，昨天的便宜可不能算今天的。'];}
  else if(event==='mission'){mood='thinking';lines=['任务收到！我帮你找候选，预算一分也不偷偷加。选好偏好再出发。'];}
  else if(event==='budget'){mood='thinking';lines=['预算改了？等下一次算完再下结论，旧账可不能冒充新账。','收到新预算。先重新算一遍，我可不靠猜来管钱包。'];}
  else if(event==='empty'){mood='confused';lines=['咦，购物篮空空的。你是来点餐，还是给菜单做阅读理解？先挑一份嘛。','先选餐品，我再帮你算。对着空气打折，这题我不会。'];}
  else if(event==='limit'){mood='shocked';lines=['先慢一点，这版最多选5种单品。咱先把这一顿算明白。'];}
  else if(event==='busy'){mood='thinking';lines=['等一下，让我把两张账单摆在一起。优惠再大，也得算完再夸。','脑袋可以放空，账单不可以。正在查实际付款，马上回来。'];}
  else if(event==='error'){mood='confused';lines=['这一步没跑通，别急着往下点。看看页面提示，改好再来，我陪你。','咦，卡了一下。失败的报价不能凑数，这笔咱重新查。'];}
  else if(event==='select'){mood='smug';lines=['先选你本来就想吃的。别让一张券，替你决定整顿饭哦。','嗯哼，餐品选好了再算。菜单价只是参考，最后付多少才算数。'];}
  else if(event==='coupon'){mood='skeptical';lines=['券已选好，可别急着宣布胜利。有没有真的少付，报价说了算。','这张券能不能立功？等我把用券前后都算一遍。'];}
  else if(event==='demo-lock'){mood='smug';lines=['这是历史案例，不是今天的菜单哦。想自己挑，去“查我的门店与券”。'];}
  else if(event==='live'){mood='idle';lines=['先选门店，再挑想吃的。我负责看账，不负责替你下单。'];}
  else{mood='idle';lines=['麦乐省钱侠到位！我不偷偷加鸡块，帮你把该省的钱算出来。你负责挑想吃的，我负责提醒别多花。','优惠券可以很会说话，我只认最后付款的数字。来，算一顿。'];}
  return {mood,text:lines[((variant%lines.length)+lines.length)%lines.length]};
 }
 root.BuddyRules={respond};
 if(typeof module!=='undefined'&&module.exports)module.exports={respond};
})(typeof globalThis!=='undefined'?globalThis:this);
