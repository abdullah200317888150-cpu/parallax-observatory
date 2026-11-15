import { useEffect, useRef, useState } from 'react';
import type { Frame, Target } from './data';

type Props={target:Target;frame:number;frames:Frame[];mode:string;grid:boolean;labels:boolean;zoom:number;exposure:number;marking:boolean;onMark:(x:number,y:number)=>void;marks:{x:number,y:number}[];live:boolean;smoothing:boolean};
export default function SkyCanvas(p:Props){
 const ref=useRef<HTMLCanvasElement>(null);const [size,setSize]=useState({w:1000,h:570});const [image,setImage]=useState<HTMLImageElement|null>(null);const [imageError,setImageError]=useState(false);
 const [pan,setPan]=useState({x:0,y:0});const drag=useRef<{x:number;y:number}|null>(null);
 useEffect(()=>{if(p.zoom===1)setPan({x:0,y:0})},[p.zoom,p.target.id,p.live]);
 useEffect(()=>{const el=ref.current!;const o=new ResizeObserver(([e])=>setSize({w:e.contentRect.width,h:e.contentRect.height}));o.observe(el);return()=>o.disconnect()},[]);
 useEffect(()=>{setImage(null);setImageError(false);const url=p.frames[p.frame]?.image;if(!url)return;const img=new Image();img.onload=()=>setImage(img);img.onerror=()=>setImageError(true);img.src=url;return()=>{img.onload=null;img.onerror=null}},[p.frames,p.frame]);
 useEffect(()=>{
  const canvas=ref.current!;const dpr=Math.min(devicePixelRatio,2);canvas.width=size.w*dpr;canvas.height=size.h*dpr;const c=canvas.getContext('2d')!;c.scale(dpr,dpr);const {w,h}=size;
  c.fillStyle='#080e15';c.fillRect(0,0,w,h);c.save();c.translate(w/2+pan.x,h/2+pan.y);c.scale(p.zoom,p.zoom);c.translate(-w/2,-h/2);
  if(p.live){if(image){c.filter=`brightness(${p.exposure})`;const side=Math.min(w,h)*.96;c.imageSmoothingEnabled=p.smoothing;c.imageSmoothingQuality='high';c.drawImage(image,(w-side)/2,(h-side)/2,side,side);c.filter='none'}}else{
   let seed=42+p.target.ra*100;const rand=()=>{seed=(seed*1664525+1013904223)%4294967296;return seed/4294967296};
   const haze=c.createRadialGradient(w*.45,h*.58,0,w*.45,h*.58,w*.58);haze.addColorStop(0,'#17222b');haze.addColorStop(.65,'#101820');haze.addColorStop(1,'#080e15');c.fillStyle=haze;c.fillRect(0,0,w,h);
   const star=(x:number,y:number,r:number,alpha:number,tint:string)=>{const g=c.createRadialGradient(x,y,0,x,y,r*5);g.addColorStop(0,`rgba(${tint},${Math.min(alpha*p.exposure,1)})`);g.addColorStop(.13,`rgba(${tint},${alpha*.7})`);g.addColorStop(.35,`rgba(${tint},${alpha*.12})`);g.addColorStop(1,`rgba(${tint},0)`);c.fillStyle=g;c.fillRect(x-r*5,y-r*5,r*10,r*10);c.fillStyle=`rgba(${tint},${Math.min(alpha*p.exposure,1)})`;c.beginPath();c.arc(x,y,r*.36,0,Math.PI*2);c.fill();if(r>2.8){c.strokeStyle=`rgba(${tint},.18)`;c.lineWidth=.5;c.beginPath();c.moveTo(x-r*7,y);c.lineTo(x+r*7,y);c.moveTo(x,y-r*7);c.lineTo(x,y+r*7);c.stroke()}};
   for(let i=0;i<1000;i++){const x=rand()*w,y=rand()*h,r=.4+Math.pow(rand(),8)*3.4,a=.2+rand()*.7;const tint=rand()>.78?'229,179,140':'193,208,220';if(p.mode!=='Difference')star(x,y,r,a,tint)}
   const f=p.frame/11;const x=w*(.49+(p.target.motion?f*.065:0)),y=h*(.49-(p.target.motion?f*.07:0));const brightness=p.target.motion?.9:.35+.6*(.5+.5*Math.sin(f*6.28));
   if(p.mode==='Difference'){star(w*.49,h*.49,4,.8,'103,172,212');star(x,y,4,brightness,'245,133,84')}else{star(x,y,4.3,brightness,'243,202,165');if(p.mode==='Compare'){c.setLineDash([4,5]);c.strokeStyle='#f16c43';c.beginPath();c.moveTo(w*.49,h*.49);c.lineTo(x,y);c.stroke();c.setLineDash([]);c.strokeRect(w*.49-10,h*.49-10,20,20)}}
   if(p.labels){c.strokeStyle='rgba(237,126,85,.8)';c.lineWidth=1;c.beginPath();c.arc(x,y,18,0,Math.PI*2);c.stroke();c.beginPath();c.moveTo(x+18,y);c.lineTo(x+54,y-30);c.lineTo(x+145,y-30);c.stroke();c.fillStyle='#f3bda5';c.font='11px monospace';c.fillText(p.target.name,x+60,y-38);c.fillStyle='#71808d';c.fillText('SIMULATED TARGET',x+60,y-16)}
  }
  c.restore();
  if(p.grid){c.strokeStyle='rgba(151,177,196,.12)';c.lineWidth=.6;for(let i=1;i<8;i++){c.beginPath();c.moveTo(w*i/8,0);c.lineTo(w*i/8,h);c.stroke()}for(let i=1;i<5;i++){c.beginPath();c.moveTo(0,h*i/5);c.lineTo(w,h*i/5);c.stroke()}}
  p.marks.forEach((m,i)=>{c.strokeStyle='#ffba77';c.lineWidth=1.5;c.beginPath();c.arc(m.x*w,m.y*h,12,0,Math.PI*2);c.stroke();c.fillStyle='#ffba77';c.font='11px monospace';c.fillText(String(i+1),m.x*w+16,m.y*h-10)});
 },[p,size,image,pan]);
 return <><canvas ref={ref} data-rendering={p.smoothing?'smooth':'pixel-exact'} className={p.marking?'sky-canvas marking':'sky-canvas'} style={{touchAction:p.zoom>1?'none':'auto',cursor:p.marking?'crosshair':p.zoom>1?'grab':'default'}} aria-label={p.live?'SPHEREx observation image':'Simulated star field for learning the viewer controls'} onPointerDown={e=>{if(p.marking||p.zoom===1)return;drag.current={x:e.clientX,y:e.clientY};e.currentTarget.setPointerCapture(e.pointerId)}} onPointerMove={e=>{if(!drag.current)return;const dx=e.clientX-drag.current.x,dy=e.clientY-drag.current.y;setPan(v=>({x:Math.max(-size.w,Math.min(size.w,v.x+dx)),y:Math.max(-size.h,Math.min(size.h,v.y+dy))}));drag.current={x:e.clientX,y:e.clientY}}} onPointerUp={()=>{drag.current=null}} onPointerCancel={()=>{drag.current=null}} onClick={e=>{if(!p.marking)return;const r=e.currentTarget.getBoundingClientRect();p.onMark((e.clientX-r.left)/r.width,(e.clientY-r.top)/r.height)}}/>{p.live&&!image&&<div className="image-loading">{imageError?'Image could not load. Try another observation.':'Loading observation…'}</div>}</>;
}
