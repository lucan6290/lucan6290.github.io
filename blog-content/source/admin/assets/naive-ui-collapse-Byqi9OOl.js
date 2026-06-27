import{D as y,I as P,V as B,bt as H,et as V,ut as O,wt as $,z as d}from"./editor-BzczECHk.js";import{Kt as K,a as q,dt as R,g as A,h as T,ht as L,i as G,p as J,pt as Q,r as X,st as Y}from"./naive-ui-alert-47JY8xkM.js";import{S as Z,_ as E,b as o,c as F,p as ee,v as x,x as g}from"./naive-ui-affix-DrKOrtjc.js";import{at as re,ot as te,st as D,z as S}from"./naive-ui-auto-complete-CCvmg59k.js";import{y as ae}from"./naive-ui-anchor-CMhXUotn.js";import{o as le}from"./naive-ui-carousel-CC-VpDyz.js";import{F as oe,I as ie}from"./naive-ui-calendar-Biu3bQ6m.js";function se(e){const{fontWeight:c,textColor1:i,textColor2:t,textColorDisabled:s,dividerColor:r,fontSize:p}=e;return{titleFontSize:p,titleFontWeight:c,dividerColor:r,titleTextColor:i,titleTextColorDisabled:s,fontSize:p,textColor:t,arrowColor:t,arrowColorDisabled:s,itemMargin:"16px 0 0 0",titlePadding:"16px 0 0 0"}}var ne={name:"Collapse",common:G,self:se},de=x("collapse","width: 100%;",[x("collapse-item",`
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition:
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 margin: var(--n-item-margin);
 `,[g("disabled",[o("header","cursor: not-allowed;",[o("header-main",`
 color: var(--n-title-text-color-disabled);
 `),x("collapse-item-arrow",`
 color: var(--n-arrow-color-disabled);
 `)])]),x("collapse-item","margin-left: 32px;"),E("&:first-child","margin-top: 0;"),E("&:first-child >",[o("header","padding-top: 0;")]),g("left-arrow-placement",[o("header",[x("collapse-item-arrow","margin-right: 4px;")])]),g("right-arrow-placement",[o("header",[x("collapse-item-arrow","margin-left: 4px;")])]),o("content-wrapper",[o("content-inner","padding-top: 16px;"),X({duration:"0.15s"})]),g("active",[o("header",[g("active",[x("collapse-item-arrow","transform: rotate(90deg);")])])]),E("&:not(:first-child)","border-top: 1px solid var(--n-divider-color);"),Z("disabled",[g("trigger-area-main",[o("header",[o("header-main","cursor: pointer;"),x("collapse-item-arrow","cursor: default;")])]),g("trigger-area-arrow",[o("header",[x("collapse-item-arrow","cursor: pointer;")])]),g("trigger-area-extra",[o("header",[o("header-extra","cursor: pointer;")])])]),o("header",`
 font-size: var(--n-title-font-size);
 display: flex;
 flex-wrap: nowrap;
 align-items: center;
 transition: color .3s var(--n-bezier);
 position: relative;
 padding: var(--n-title-padding);
 color: var(--n-title-text-color);
 `,[o("header-main",`
 display: flex;
 flex-wrap: nowrap;
 align-items: center;
 font-weight: var(--n-title-font-weight);
 transition: color .3s var(--n-bezier);
 flex: 1;
 color: var(--n-title-text-color);
 `),o("header-extra",`
 display: flex;
 align-items: center;
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),x("collapse-item-arrow",`
 display: flex;
 transition:
 transform .15s var(--n-bezier),
 color .3s var(--n-bezier);
 font-size: 18px;
 color: var(--n-arrow-color);
 `)])])]),ce=Object.assign(Object.assign({},T.props),{defaultExpandedNames:{type:[Array,String],default:null},expandedNames:[Array,String],arrowPlacement:{type:String,default:"left"},accordion:{type:Boolean,default:!1},displayDirective:{type:String,default:"if"},triggerAreas:{type:Array,default:()=>["main","extra","arrow"]},onItemHeaderClick:[Function,Array],"onUpdate:expandedNames":[Function,Array],onUpdateExpandedNames:[Function,Array],onExpandedNamesChange:{type:[Function,Array],validator:()=>!0,default:void 0}}),k=ee("n-collapse"),we=P({name:"Collapse",props:ce,slots:Object,setup(e,{slots:c}){const{mergedClsPrefixRef:i,inlineThemeDisabled:t,mergedRtlRef:s}=F(e),r=H(e.defaultExpandedNames),p=re(y(()=>e.expandedNames),r),v=T("Collapse","-collapse",de,ne,e,i);function m(u){const{"onUpdate:expandedNames":l,onUpdateExpandedNames:h,onExpandedNamesChange:b}=e;h&&S(h,u),l&&S(l,u),b&&S(b,u),r.value=u}function f(u){const{onItemHeaderClick:l}=e;l&&S(l,u)}function a(u,l,h){const{accordion:b}=e,{value:_}=p;if(b)u?(m([l]),f({name:l,expanded:!0,event:h})):(m([]),f({name:l,expanded:!1,event:h}));else if(!Array.isArray(_))m([l]),f({name:l,expanded:!0,event:h});else{const C=_.slice(),I=C.findIndex(z=>l===z);~I?(C.splice(I,1),m(C),f({name:l,expanded:!1,event:h})):(C.push(l),m(C),f({name:l,expanded:!0,event:h}))}}V(k,{props:e,mergedClsPrefixRef:i,expandedNamesRef:p,slots:c,toggleItem:a});const n=A("Collapse",s,i),N=y(()=>{const{common:{cubicBezierEaseInOut:u},self:{titleFontWeight:l,dividerColor:h,titlePadding:b,titleTextColor:_,titleTextColorDisabled:C,textColor:I,arrowColor:z,fontSize:U,titleFontSize:j,arrowColorDisabled:M,itemMargin:W}}=v.value;return{"--n-font-size":U,"--n-bezier":u,"--n-text-color":I,"--n-divider-color":h,"--n-title-padding":b,"--n-title-font-size":j,"--n-title-text-color":_,"--n-title-text-color-disabled":C,"--n-title-font-weight":l,"--n-arrow-color":z,"--n-arrow-color-disabled":M,"--n-item-margin":W}}),w=t?Y("collapse",void 0,N,e):void 0;return{rtlEnabled:n,mergedTheme:v,mergedClsPrefix:i,cssVars:t?void 0:N,themeClass:w?.themeClass,onRender:w?.onRender}},render(){var e;return(e=this.onRender)===null||e===void 0||e.call(this),d("div",{class:[`${this.mergedClsPrefix}-collapse`,this.rtlEnabled&&`${this.mergedClsPrefix}-collapse--rtl`,this.themeClass],style:this.cssVars},this.$slots)}}),pe=P({name:"CollapseItemContent",props:{displayDirective:{type:String,required:!0},show:Boolean,clsPrefix:{type:String,required:!0}},setup(e){return{onceTrue:te($(e,"show"))}},render(){return d(q,null,{default:()=>{const{show:e,displayDirective:c,onceTrue:i,clsPrefix:t}=this,s=c==="show"&&i,r=d("div",{class:`${t}-collapse-item__content-wrapper`},d("div",{class:`${t}-collapse-item__content-inner`},this.$slots));return s?O(r,[[K,e]]):e?r:null}})}}),me={title:String,name:[String,Number],disabled:Boolean,displayDirective:String},be=P({name:"CollapseItem",props:me,setup(e){const{mergedRtlRef:c}=F(e),i=le(),t=ae(()=>{var a;return(a=e.name)!==null&&a!==void 0?a:i}),s=B(k);s||L("collapse-item","`n-collapse-item` must be placed inside `n-collapse`.");const{expandedNamesRef:r,props:p,mergedClsPrefixRef:v,slots:m}=s,f=y(()=>{const{value:a}=r;if(Array.isArray(a)){const{value:n}=t;return!~a.findIndex(N=>N===n)}else if(a){const{value:n}=t;return n!==a}return!0});return{rtlEnabled:A("Collapse",c,v),collapseSlots:m,randomName:i,mergedClsPrefix:v,collapsed:f,triggerAreas:$(p,"triggerAreas"),mergedDisplayDirective:y(()=>{const{displayDirective:a}=e;return a||p.displayDirective}),arrowPlacement:y(()=>p.arrowPlacement),handleClick(a){let n="main";D(a,"arrow")&&(n="arrow"),D(a,"extra")&&(n="extra"),p.triggerAreas.includes(n)&&s&&!e.disabled&&s.toggleItem(f.value,t.value,a)}}},render(){const{collapseSlots:e,$slots:c,arrowPlacement:i,collapsed:t,mergedDisplayDirective:s,mergedClsPrefix:r,disabled:p,triggerAreas:v}=this,m=R(c.header,{collapsed:t},()=>[this.title]),f=c["header-extra"]||e["header-extra"],a=c.arrow||e.arrow;return d("div",{class:[`${r}-collapse-item`,`${r}-collapse-item--${i}-arrow-placement`,p&&`${r}-collapse-item--disabled`,!t&&`${r}-collapse-item--active`,v.map(n=>`${r}-collapse-item--trigger-area-${n}`)]},d("div",{class:[`${r}-collapse-item__header`,!t&&`${r}-collapse-item__header--active`]},d("div",{class:`${r}-collapse-item__header-main`,onClick:this.handleClick},i==="right"&&m,d("div",{class:`${r}-collapse-item-arrow`,key:this.rtlEnabled?0:1,"data-arrow":!0},R(a,{collapsed:t},()=>[d(J,{clsPrefix:r},{default:()=>this.rtlEnabled?d(ie,null):d(oe,null)})])),i==="left"&&m),Q(f,{collapsed:t},n=>d("div",{class:`${r}-collapse-item__header-extra`,onClick:this.handleClick,"data-extra":!0},n))),d(pe,{clsPrefix:r,displayDirective:s,show:!t},c))}});export{ce as i,me as n,we as r,be as t};
