/* UI for the original mascot. Text only, no speech synthesis or remote models. */
(()=>{
 const dock=document.getElementById('buddy');if(!dock)return;
 const line=document.getElementById('buddy-line');const label=document.getElementById('buddy-context');
 const pause=document.getElementById('buddy-pause');const collapse=document.getElementById('buddy-collapse');
 let paused=false,last={event:'hello',payload:{}},variant=0,pending=null;
 try{paused=localStorage.getItem('mcd-buddy-paused')==='true';dock.classList.toggle('collapsed',localStorage.getItem('mcd-buddy-collapsed')==='true');}catch{}
 function remember(key,value){try{localStorage.setItem(key,String(value));}catch{}}
 function setLine(event,payload={},manual=false){
  if(paused&&!manual)return;
  const reply=BuddyRules.respond(event,payload,variant);
  dock.dataset.mood=reply.mood;line.textContent=reply.text;
  label.textContent=event==='result'?(payload.mode==='live'?'跟着这轮报价说':payload.case==='extra'?'模拟案例，演给你看':'跟着历史实测说'):'跟着你的操作说';
  dock.classList.remove('reacting');void dock.offsetWidth;dock.classList.add('reacting');
 }
 function pauseUI(){pause.textContent=paused?'恢复吐槽':'暂停吐槽';pause.setAttribute('aria-pressed',String(paused));document.getElementById('buddy-more').disabled=paused;}
 pause.addEventListener('click',()=>{paused=!paused;remember('mcd-buddy-paused',paused);pauseUI();if(paused){line.textContent='好啦，我安静站岗。有需要再叫我。';dock.dataset.mood='idle';label.textContent='吐槽已暂停';}else{variant=0;setLine(last.event,last.payload);}});
 collapse.addEventListener('click',()=>{const hidden=dock.classList.toggle('collapsed');collapse.textContent=hidden?'展开':'收起';collapse.setAttribute('aria-expanded',String(!hidden));remember('mcd-buddy-collapsed',hidden);});
 document.getElementById('buddy-more').addEventListener('click',()=>{variant++;setLine(last.event,last.payload);});
 document.getElementById('buddy-character').addEventListener('click',()=>{if(!paused){variant++;setLine(last.event,last.payload);}});
 window.addEventListener('mcd:buddy',e=>{
  clearTimeout(pending);last={event:e.detail.event,payload:e.detail.payload||{}};variant=0;
  if(last.event==='budget')pending=setTimeout(()=>setLine(last.event,last.payload),500);
  else setLine(last.event,last.payload);
 });
 const collapsed=dock.classList.contains('collapsed');collapse.textContent=collapsed?'展开':'收起';collapse.setAttribute('aria-expanded',String(!collapsed));pauseUI();
 if(paused){line.textContent='我先安静站岗。有需要再叫我。';label.textContent='吐槽已暂停';}else setLine('hello');
})();
