import type { Frame } from './data';

export default function ImageDisplayOptions({smooth,onChange,frame,fov}:{smooth:boolean;onChange:(value:boolean)=>void;frame:Frame;fov:number}) {
 const scale=frame.native_pixel_scale_arcsec||6.15;
 const pixels=Math.round(fov*60/scale);
 return <div className="image-display-options">
  <div className="rendering-controls"><span className="small-label">IMAGE DISPLAY</span><div className="segmented" role="group" aria-label="Image rendering"><button aria-pressed={smooth} className={smooth?'active':''} onClick={()=>onChange(true)}>Smooth</button><button aria-pressed={!smooth} className={!smooth?'active':''} onClick={()=>onChange(false)}>Pixel-exact</button></div></div>
  <p>Approx. {pixels} native pixels across · {scale.toFixed(2)}″/pixel. Smoothing changes appearance only. Dark gaps are masked or missing data.</p>
 </div>;
}
