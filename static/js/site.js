$(document).ready(function() {
  function guessedCorrectly(expected, guess) {
      console.log(expected);
      console.log(guess);
      return (0 <= expected < 10) && (expected == guess)
  }

  function updateGuess(corrected, identifier) {
    $.ajax({
      url: '/api/drawings/' + identifier.toString(),
      method: 'PATCH',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify({digit: corrected}),
      success: function(){
        alert("Understood! Thank you for correcting me!");
      }
    });
  }

  function onSubmitDrawing(event){
    $.ajax({
        url: '/api/drawings',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({img: document.getElementById('simple_sketch').toDataURL()}),
        success: function(data){
          var message = "Nice drawing, is that " + data.guess.toString() + "?";
          var correct_digit = prompt(message, data.guess);
          if (typeof(correct_digit) !== "undefined" || correct_digit == null) {
            correct_digit = parseInt(correct_digit, 10);
            if (Number.isInteger(correct_digit) && !guessedCorrectly(correct_digit, data.guess)) {
                updateGuess(correct_digit, data.id);
            }
          }
        }
    });
  };

  $('#submit_drawing_button').on('click', onSubmitDrawing);

});
