var x=0,y=0;
function hide_header_content()
{
if (x==0)
    {
    header_content.style.display = 'none';
    header_content_background_right.style.display = 'none';
    header_content_background_middle.style.display = 'none';
    header_content_background_left.style.display = 'none';
    line1.style.display = 'none';
    line2.style.display = 'none';
    header_botton.src = "images/botton_down.gif";
    x=1;
    }
else
    {
    header_content.style.display = 'block';
    header_content_background_right.style.display = 'block';
    header_content_background_middle.style.display = 'block';
    header_content_background_left.style.display = 'block';
    line1.style.display = 'block';
    line2.style.display = 'block';
    header_botton.src = "images/botton_top.gif";
    x=0;
    }
}



function hide_reply(i) {
var content = document.getElementById('reply'+i+'_content');
var button  = document.getElementById('reply'+i+'_button');
if (y==0)
    {
    content.style.display = 'none';
    button.src = "images/botton_down.gif";
    y=1;
    }
else
    {
    content.style.display = 'block';
    button.src = "images/botton_top.gif";
    y=0;
    }
}

function setEghdam(txt)
{
    if(txt=="")
    {
    }
    else
    {
        eghdam_text.innerHTML = txt;
        document.getElementById('eghdam_image').style.display="inline";
    }
}

function setBarValue(element, value, maxValue)
{
    value = parseInt(value);
    var s = "";
    for(var i=maxValue-value;i<maxValue;i++)
    {
       s += '<img src="images/on.jpg" style="margin-left:1px" />';
       }
    for(var i=0;i<maxValue-value;i++)
    {
       s += '<img src="images/off.jpg" style="margin-left:1px" />';
    }
    element.innerHTML = s;
}

function setAttachments()
{
    var nn=5;
    var args = setAttachments.arguments;
    var n = (args.length)/nn ;
    if( n==0)
    {
        attachmentsRow.style.display = 'none';
        return;    
    }
    var str = '';
    for(var i=0;i<n;i++)
    {
        var i0 = i*nn;
        str += "<span onmousedown='javascript:window.external.ShowAttachment(" + args[i0+3] + ")' class="+args[i0+0]+"> ";
        str += "(<span dir=rtl >" + args[i0+2] + "</span>)&nbsp;";
        str += "<span dir=ltr >" +args[i0+1] + "</span>";
        //str += "(10k)&nbsp;";
        str += '&nbsp;<img src="' + args[i0+4] + '" style="margin:0px 0px 0px 2px; vertical-align:middle" /> '
        str += "</span>";
        
        if( i<n-1 )
            str += ';';
    }
    attachments.innerHTML = str;
}

function SwitchHistoryVis()
{
}
