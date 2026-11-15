export type Target = {id:string; name:string; kind:string; ra:number; dec:number; description:string; motion:boolean; color:string};
export const targets:Target[] = [
 {id:'barnard',name:"Barnard’s Star",kind:'HIGH PROPER MOTION STAR',ra:269.4521,dec:4.6934,description:'A nearby star with a remarkable journey across our sky. Compare observations to look for its motion against the distant background.',motion:true,color:'#dcaa83'},
 {id:'epsilon',name:'Epsilon Indi B',kind:'BROWN DWARF PAIR',ra:330.8417,dec:-56.7858,description:'Two cool brown dwarfs orbiting a nearby star. At SPHEREx resolution, this close pair may appear as a single source.',motion:true,color:'#c59772'},
 {id:'wise',name:'WISE 0855',kind:'ULTRACOOL BROWN DWARF',ra:133.795129,dec:-7.245147,description:'A cold, faint neighbor best explored in infrared. Its changing apparent position makes it an intriguing target for time-domain astronomy.',motion:true,color:'#8baab4'},
 {id:'rw',name:'RW Aurigae',kind:'VARIABLE YOUNG STAR',ra:76.9565,dec:30.4014,description:'A young stellar system that varies in brightness. Watch for changes in light as well as changes in position.',motion:false,color:'#d39a9a'},
 {id:'rdraconis',name:'R Draconis',kind:'VARIABLE GIANT STAR',ra:248.4804,dec:66.7527,description:'A pulsating giant star. Compare observations at similar wavelengths to investigate changes in its brightness.',motion:false,color:'#c7a47d'},
];
export type Frame = {id:string;date:string; image?:string;source_url?:string;wavelength?:number|null;flagged_fraction?:number;version?:string;native_width?:number;native_height?:number;native_pixel_scale_arcsec?:number};
export const demoFrames:Frame[] = Array.from({length:12},(_,i)=>({id:`demo-${i}`,date:new Date(Date.UTC(2025,4,20+i*16)).toISOString(),wavelength:null}));
export type Observation = {id:string;date:string;source_url:string};
