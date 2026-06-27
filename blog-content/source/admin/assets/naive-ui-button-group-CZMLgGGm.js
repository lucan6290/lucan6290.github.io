import{I as c,et as p,z as g}from"./editor-BzczECHk.js";import{g as b}from"./naive-ui-alert-47JY8xkM.js";import{S as d,_ as o,b as s,c as m,i as h,v as n,x as e}from"./naive-ui-affix-DrKOrtjc.js";import{a as $}from"./naive-ui-button-C6uUobda.js";var r="0!important",u="-1px!important";function i(t){return e(`${t}-type`,[o("& +",[n("button",{},[e(`${t}-type`,[s("border",{borderLeftWidth:r}),s("state-border",{left:u})])])])])}function a(t){return e(`${t}-type`,[o("& +",[n("button",[e(`${t}-type`,[s("border",{borderTopWidth:r}),s("state-border",{top:u})])])])])}var v=n("button-group",`
 flex-wrap: nowrap;
 display: inline-flex;
 position: relative;
`,[d("vertical",{flexDirection:"row"},[d("rtl",[n("button",[o("&:first-child:not(:last-child)",`
 margin-right: ${r};
 border-top-right-radius: ${r};
 border-bottom-right-radius: ${r};
 `),o("&:last-child:not(:first-child)",`
 margin-left: ${r};
 border-top-left-radius: ${r};
 border-bottom-left-radius: ${r};
 `),o("&:not(:first-child):not(:last-child)",`
 margin-left: ${r};
 margin-right: ${r};
 border-radius: ${r};
 `),i("default"),e("ghost",[i("primary"),i("info"),i("success"),i("warning"),i("error")])])])]),e("vertical",{flexDirection:"column"},[n("button",[o("&:first-child:not(:last-child)",`
 margin-bottom: ${r};
 margin-left: ${r};
 margin-right: ${r};
 border-bottom-left-radius: ${r};
 border-bottom-right-radius: ${r};
 `),o("&:last-child:not(:first-child)",`
 margin-top: ${r};
 margin-left: ${r};
 margin-right: ${r};
 border-top-left-radius: ${r};
 border-top-right-radius: ${r};
 `),o("&:not(:first-child):not(:last-child)",`
 margin: ${r};
 border-radius: ${r};
 `),a("default"),e("ghost",[a("primary"),a("info"),a("success"),a("warning"),a("error")])])])]),x={size:String,vertical:Boolean},G=c({name:"ButtonGroup",props:x,setup(t){const{mergedClsPrefixRef:l,mergedRtlRef:f}=m(t);return h("-button-group",v,l),p($,t),{rtlEnabled:b("ButtonGroup",f,l),mergedClsPrefix:l}},render(){const{mergedClsPrefix:t}=this;return g("div",{class:[`${t}-button-group`,this.rtlEnabled&&`${t}-button-group--rtl`,this.vertical&&`${t}-button-group--vertical`],role:"group"},this.$slots)}});export{x as n,G as t};
