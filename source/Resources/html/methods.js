function myClick(number, state)
{
    var body= document.getElementById("body"+number);
    var img= document.getElementById("img"+number);
    
    if( state==true || (state==undefined && body.style.display == "none" ) )
    {//Open
        body.style.display = "block";
        img.src = "close.png";
    }
    else if( state==false || (state==undefined && body.style.display == "block" ) )
    {//close
        body.style.display = "none";
        img.src = "open.png";
    }
}
function doForAll(openState)
{
    var list=document.getElementsByName("expander");
    for(var i=0;i<list.length;i++)
    {
        myClick(i,openState);        
    }
}

var doOpenAllState='opened';
function DoOpenAll()
{
    var button = document.getElementById("openAll");
    if( doOpenAllState=='opened')
    {
        doOpenAllState='closed'
        doForAll(0);
        button.innerText = 'نمايش مشروح';
    }
    else
    {
        doOpenAllState='opened';
        doForAll(1);
        button.innerText = 'نمايش خلاصه';
    }
}

function SwitchHistoryVis()
{
    var hist = document.getElementById('HistoryBody');
    if( hist == null)
        return;
    
    var openBtn = document.getElementById('openAll');
    var visBtn = document.getElementById('SwitchHistoryVisTag');
    var imgHistory = document.getElementById('imgHistory');
    

    if( hist.style.display != "none")
    {
        hist.style.display = "none"
        openBtn.style.display = "none"
        visBtn.innerText = "نمايش سابقه"
        imgHistory.src = "open.png";
    } 
    else
    {
        hist.style.display = "block"
        openBtn.style.display = "block"
        visBtn.innerText = "عدم نمايش سابقه"
        imgHistory.src = "close.png";
    }
    
    javascript:window.external.SetHistoryOpen( hist.style.display != "none" )
}
