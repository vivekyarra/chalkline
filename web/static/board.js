export function imageFromBase64(value) {
  return new Promise((resolve, reject) => { const img = new Image(); img.onload=()=>resolve(img); img.onerror=reject; img.src=`data:image/png;base64,${value}`; });
}
async function tileIsValid(tile){
  if(!tile.sha256)return true;
  const raw=Uint8Array.from(atob(tile.png),c=>c.charCodeAt(0));
  const digest=await crypto.subtle.digest('SHA-256',raw);
  return [...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('')===tile.sha256;
}
export class BoardClient {
  constructor(canvas, staleCanvas, onState) { this.canvas=canvas; this.ctx=canvas.getContext('2d'); this.stale=staleCanvas; this.onState=onState; this.version=-1; this.epoch=null; this.liveImage=null; }
  async checkpoint(m) { this.canvas.width=m.width; this.canvas.height=m.height; this.stale.width=m.width; this.stale.height=m.height; const img=await imageFromBase64(m.image); this.ctx.drawImage(img,0,0); this.liveImage=m.image; this.version=m.version; this.epoch=m.epoch; await this.drawStale(m.stale_mask); this.onState('LIVE',m.version); }
  async patch(m, ws) { if(m.epoch!==this.epoch || m.base_version!==this.version || !(await Promise.all(m.tiles.map(tileIsValid))).every(Boolean)){ ws.send(JSON.stringify({type:'resync',version:this.version,epoch:this.epoch})); this.onState('SYNCING',this.version); return; } const decoded=await Promise.all(m.tiles.map(async t=>({t,img:await imageFromBase64(t.png)}))); for(const {t,img} of decoded)this.ctx.drawImage(img,t.x,t.y,t.w,t.h); this.version=m.version; await this.drawStale(m.stale_mask); this.onState('LIVE',m.version); }
  async drawStale(value){ if(!value)return; const img=await imageFromBase64(value), c=this.stale.getContext('2d'); c.clearRect(0,0,this.stale.width,this.stale.height); c.drawImage(img,0,0,this.stale.width,this.stale.height); }
}
