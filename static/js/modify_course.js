 $(function(){
  $('input[id=couse]').blur(function(){
    val=this.value;
    if(val.length==0){
      $('.nll').show();
    }
    else{
      $('.nll').hide();
    }
});
});