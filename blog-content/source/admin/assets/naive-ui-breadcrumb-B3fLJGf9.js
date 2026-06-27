import{D as p,I as g,V as P,X as T,Z as L,bt as y,et as S,wt as j,z as v}from"./editor-BzczECHk.js";import{h as x,i as H,st as w,ut as I}from"./naive-ui-alert-47JY8xkM.js";import{_ as s,b as u,c as E,p as O,v as m,x as $}from"./naive-ui-affix-DrKOrtjc.js";import{X as A}from"./naive-ui-auto-complete-CCvmg59k.js";var V={fontWeightActive:"400"};function D(e){const{fontSize:o,textColor3:a,textColor2:r,borderRadius:i,buttonColor2Hover:t,buttonColor2Pressed:l}=e;return Object.assign(Object.assign({},V),{fontSize:o,itemLineHeight:"1.25",itemTextColor:a,itemTextColorHover:r,itemTextColorPressed:r,itemTextColorActive:r,itemBorderRadius:i,itemColorHover:t,itemColorPressed:l,separatorColor:a})}var K={name:"Breadcrumb",common:H,self:D},M=m("breadcrumb",`
 white-space: nowrap;
 cursor: default;
 line-height: var(--n-item-line-height);
`,[s("ul",`
 list-style: none;
 padding: 0;
 margin: 0;
 `),s("a",`
 color: inherit;
 text-decoration: inherit;
 `),m("breadcrumb-item",`
 font-size: var(--n-font-size);
 transition: color .3s var(--n-bezier);
 display: inline-flex;
 align-items: center;
 `,[m("icon",`
 font-size: 18px;
 vertical-align: -.2em;
 transition: color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 `),s("&:not(:last-child)",[$("clickable",[u("link",`
 cursor: pointer;
 `,[s("&:hover",`
 background-color: var(--n-item-color-hover);
 `),s("&:active",`
 background-color: var(--n-item-color-pressed); 
 `)])])]),u("link",`
 padding: 4px;
 border-radius: var(--n-item-border-radius);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 position: relative;
 `,[s("&:hover",`
 color: var(--n-item-text-color-hover);
 `,[m("icon",`
 color: var(--n-item-text-color-hover);
 `)]),s("&:active",`
 color: var(--n-item-text-color-pressed);
 `,[m("icon",`
 color: var(--n-item-text-color-pressed);
 `)])]),u("separator",`
 margin: 0 8px;
 color: var(--n-separator-color);
 transition: color .3s var(--n-bezier);
 user-select: none;
 -webkit-user-select: none;
 `),s("&:last-child",[u("link",`
 font-weight: var(--n-font-weight-active);
 cursor: unset;
 color: var(--n-item-text-color-active);
 `,[m("icon",`
 color: var(--n-item-text-color-active);
 `)]),u("separator",`
 display: none;
 `)])])]),C=O("n-breadcrumb"),X=Object.assign(Object.assign({},x.props),{separator:{type:String,default:"/"}}),J=g({name:"Breadcrumb",props:X,setup(e){const{mergedClsPrefixRef:o,inlineThemeDisabled:a}=E(e),r=x("Breadcrumb","-breadcrumb",M,K,e,o);S(C,{separatorRef:j(e,"separator"),mergedClsPrefixRef:o});const i=p(()=>{const{common:{cubicBezierEaseInOut:l},self:{separatorColor:d,itemTextColor:n,itemTextColorHover:c,itemTextColorPressed:b,itemTextColorActive:h,fontSize:f,fontWeightActive:B,itemBorderRadius:R,itemColorHover:k,itemColorPressed:z,itemLineHeight:_}}=r.value;return{"--n-font-size":f,"--n-bezier":l,"--n-item-text-color":n,"--n-item-text-color-hover":c,"--n-item-text-color-pressed":b,"--n-item-text-color-active":h,"--n-separator-color":d,"--n-item-color-hover":k,"--n-item-color-pressed":z,"--n-item-border-radius":R,"--n-font-weight-active":B,"--n-item-line-height":_}}),t=a?w("breadcrumb",void 0,i,e):void 0;return{mergedClsPrefix:o,cssVars:a?void 0:i,themeClass:t?.themeClass,onRender:t?.onRender}},render(){var e;return(e=this.onRender)===null||e===void 0||e.call(this),v("nav",{class:[`${this.mergedClsPrefix}-breadcrumb`,this.themeClass],style:this.cssVars,"aria-label":"Breadcrumb"},v("ul",null,this.$slots))}});function F(e=A?window:null){const o=()=>{const{hash:i,host:t,hostname:l,href:d,origin:n,pathname:c,port:b,protocol:h,search:f}=e?.location||{};return{hash:i,host:t,hostname:l,href:d,origin:n,pathname:c,port:b,protocol:h,search:f}},a=y(o()),r=()=>{a.value=o()};return T(()=>{e&&(e.addEventListener("popstate",r),e.addEventListener("hashchange",r))}),L(()=>{e&&(e.removeEventListener("popstate",r),e.removeEventListener("hashchange",r))}),a}var N={separator:String,href:String,clickable:{type:Boolean,default:!0},showSeparator:{type:Boolean,default:!0},onClick:Function},Q=g({name:"BreadcrumbItem",props:N,slots:Object,setup(e,{slots:o}){const a=P(C,null);if(!a)return()=>null;const{separatorRef:r,mergedClsPrefixRef:i}=a,t=F(),l=p(()=>e.href?"a":"span"),d=p(()=>t.value.href===e.href?"location":null);return()=>{const{value:n}=i;return v("li",{class:[`${n}-breadcrumb-item`,e.clickable&&`${n}-breadcrumb-item--clickable`]},v(l.value,{class:`${n}-breadcrumb-item__link`,"aria-current":d.value,href:e.href,onClick:e.onClick},o),e.showSeparator&&v("span",{class:`${n}-breadcrumb-item__separator`,"aria-hidden":"true"},I(o.separator,()=>{var c;return[(c=e.separator)!==null&&c!==void 0?c:r.value]})))}}});export{X as i,N as n,J as r,Q as t};
