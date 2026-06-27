import{D as l,I as u,et as g,z as v}from"./editor-BzczECHk.js";import{g as f,h as c,i as h,m as x}from"./naive-ui-alert-47JY8xkM.js";import{S as m,_ as i,c as O,v as n,x as p}from"./naive-ui-affix-DrKOrtjc.js";import{i as A,r as y,t as d}from"./naive-ui-avatar-Dkkn1t0c.js";function b(){return{gap:"-12px"}}var G=x({name:"AvatarGroup",common:h,peers:{Avatar:A},self:b}),_=n("avatar-group",`
 flex-wrap: nowrap;
 display: inline-flex;
 position: relative;
`,[p("expand-on-hover",[n("avatar",[i("&:not(:first-child)",`
 transition: margin .3s var(--n-bezier);
 `)]),i("&:hover",[m("vertical",[n("avatar",[i("&:not(:first-child)",`
 margin-left: 0 !important;
 `)])]),p("vertical",[n("avatar",[i("&:not(:first-child)",`
 margin-top: 0 !important;
 `)])])])]),m("vertical",`
 flex-direction: row;
 `,[n("avatar",[i("&:not(:first-child)",`
 margin-left: var(--n-gap);
 `)])]),p("vertical",`
 flex-direction: column;
 `,[n("avatar",[i("&:not(:first-child)",`
 margin-top: var(--n-gap);
 `)])])]),$=Object.assign(Object.assign({},c.props),{max:Number,maxStyle:[Object,String],options:{type:Array,default:()=>[]},vertical:Boolean,expandOnHover:Boolean,size:[String,Number]}),T=u({name:"AvatarGroup",props:$,slots:Object,setup(a){const{mergedClsPrefixRef:o,mergedRtlRef:t}=O(a),s=c("AvatarGroup","-avatar-group",_,G,a,o);return g(y,a),{mergedTheme:s,rtlEnabled:f("AvatarGroup",t,o),mergedClsPrefix:o,restOptions:l(()=>{const{max:r}=a;if(r===void 0)return;const{options:e}=a;return e.length>r?e.slice(r-1,e.length):[]}),displayedOptions:l(()=>{const{options:r,max:e}=a;return e===void 0?r:r.length>e?r.slice(0,e-1):r.length===e?r.slice(0,e):r}),cssVars:l(()=>({"--n-gap":s.value.self.gap}))}},render(){const{mergedClsPrefix:a,displayedOptions:o,restOptions:t,mergedTheme:s,$slots:r}=this;return v("div",{class:[`${a}-avatar-group`,this.rtlEnabled&&`${a}-avatar-group--rtl`,this.vertical&&`${a}-avatar-group--vertical`,this.expandOnHover&&`${a}-avatar-group--expand-on-hover`],style:this.cssVars,role:"group"},o.map(e=>r.avatar?r.avatar({option:e}):v(d,{src:e.src,theme:s.peers.Avatar,themeOverrides:s.peerOverrides.Avatar})),t!==void 0&&t.length>0&&(r.rest?r.rest({options:t,rest:t.length}):v(d,{style:this.maxStyle,theme:s.peers.Avatar,themeOverrides:s.peerOverrides.Avatar},{default:()=>`+${t.length}`})))}});export{$ as n,T as t};
