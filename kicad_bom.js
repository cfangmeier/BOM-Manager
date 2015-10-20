<script>
function find_price_break(price_breaks, n){
  price_breaks = price_breaks.split(';');
  var num_breaks = price_breaks.length
  for(var i=0; i<num_breaks; i++){
    var break_high = price_breaks[i].split('@');
    var break_high_n = Number(break_high[0]);
    var break_high_price = Number(break_high[1]);
    if(i == 0){
      if(n < break_high_n){
        return Number("NaN");
      }
      else{
        continue;
      }
    }
    var break_low = price_breaks[i-1].split('@');
    var break_low_n = Number(break_low[0]);
    var break_low_price = Number(break_low[1]);
    if(break_low_n<=n && n < break_high_n){
      return break_low_price;
    }
  }
  var break_highest = price_breaks[num_breaks-1].split('@');
  var break_highest_price = Number(break_high[1]);
  return break_highest_price
}

function update_tottot(){
  var prices = $('.price').text().split('$');
  var sum = 0.0;
  for(var i=0; i<prices.length;i++){
    sum += Number(prices[i]);
  }
  $('#pricetot').text('$'+sum.toFixed(6))
}

function cleanUp(a) {
  a.textContent = 'Downloaded';
//  a.dataset.disabled = true;
  $(a).attr('data-disabled', true);

  // Need a small delay for the revokeObjectURL to work properly.
  setTimeout(function() {
    window.URL.revokeObjectURL(a.href);
    $(a).remove()
  }, 1500);
};

function generateFile(){
  console.log("generating file");
  var objs = [];
  $('tr.datarow').each( function(){
    var data = $(this).children();
    var obj = {
      part_number: $(data[2]).text(),
      description: $(data[1]).text(),
      unit_price: $(data[8]).text(),
      total_price: $(data[9]).text(),
      num_order: $(data[7]).children()[0].value,
    };
    objs.push(obj);
  });
//    console.log(JSON.stringify(objs));
    return JSON.stringify(objs);
}

function downloadFile(){
  console.log("preparing file for download");
  window.URL = window.webkitURL || window.URL;

  var prevLink = $('#outlink');
  var output = $('#output');
  if (prevLink) {
    window.URL.revokeObjectURL(prevLink.href);
    output.innerHTML = '';
  }

  var bb = new Blob([generateFile()], {type: "application/json"});

  var a = $('<a id=\\\'outlink\\\'>Download ready</a>');
  a.attr('download',$('#filename').attr('value'));
  a.attr('href',window.URL.createObjectURL(bb));

  a.attr('data-downloadurl', ["application/json", a.download, a.href].join(':'));
  a.draggable = true; // Don't really need, but good practice.
  a.addClass('dragout');

  output.prepend(a);

  a.on('click', function(e) {
    if ('disabled' in this.dataset) {
      return false;
    }

    cleanUp(this);
  });
}

$('input').on('focus', function(){
  $(this).parent().parent().addClass('select');
});

$('input').on('blur', function(){
  $(this).parent().parent().removeClass('select');
});

$('input').on('keypress', function(event) {
  if(event.type == 'keypress'){
    var key = event.charCode || event.keyCode;
    if(key == 13){ // ie. Return
      return;
    }
  }
  $(this).css('background-color', '#FFCCFF');
  });

$('input').on('change keypress', function(event) {
  if(event.type == 'keypress'){
    var key = event.charCode || event.keyCode;
    if(key != 13){ // ie. Not Return
      return;
    }
  }
  $(this).css('background-color', '#FFFFFF');
  var n = Number($(this).val());
  if(Number.isNaN(n)){
    return;
  }
  var id_base = $(this).attr('id').split('_')[0];
  var priceper_field = $('#'+id_base+'_priceper')
  var price_field = $('#'+id_base+'_price')
  var priceper = find_price_break(priceper_field.attr('title'),n);
  var price = priceper*n;
  priceper_field.text('$'+priceper.toFixed(6));
  price_field.text('$'+price.toFixed(6));
  update_tottot();
});
</script>
