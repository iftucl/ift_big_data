auth_header_template = """
<script>
$(document).ready(function() {
 // executes when HTML-Document is loaded and DOM is ready

// breakpoint and up  
$(window).resize(function(){
	if ($(window).width() >= 980){	

      // when you hover a toggle show its dropdown menu
      $(".navbar .dropdown-toggle").hover(function () {
         $(this).parent().toggleClass("show");
         $(this).parent().find(".dropdown-menu").toggleClass("show"); 
       });

        // hide the menu when the mouse leaves the dropdown
      $( ".navbar .dropdown-menu" ).mouseleave(function() {
        $(this).removeClass("show");  
      });
  
		// do something here
	}	
});
// document ready  
});
</script>
<header>
    <nav class="navbar navbar-expand-lg">
        <div class="navbar-brand">Hello,<b> USERNAME_PLACEHOLDER - GROUP_PLACEHOLDER</b></div>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
    <div class="collapse navbar-collapse justify-content-end" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto">
        <li class="nav-item">
            <a class="nav-link" href="/">Home</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="#">About</a>
        </li>        
        <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/scarp/paift" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                paift
            </a>
            <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                <div class="container">
                    <div class="row">
                        <div class="col-md-3">
                            <span class="text-uppercase text-white">
                                <div class="container section-title">
                                    <a class="nav-link active" href="/scarp/paift">
                                        <h2>PA-IFT</h2>
                                    </a>
                                </div>
                            </span>
                        </div>
                        <div class="col-md-3">
                            <ul class="nav flex-column">
                                <li class="nav-item">
                                    <div class="container section-title-column">
                                        <h3>
                                            <a class="nav-link active" href="/scarp/paift">INPUT</a>
                                        </h3>
                                    </div>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/">Under Construction</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href=""></a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href=""></a>
                                </li>
                            </ul>
                        </div>
                        <!-- /.col-md-3  -->
                        <div class="col-md-3">
                            <ul class="nav flex-column">
                                <li class="nav-item">
                                    <div class="container section-title-column">
                                        <h3>
                                            <a class="nav-link active" href="/scarp/paift">Portfolio Analytics</a>
                                        </h3>
                                    </div>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/scarp/paift">Under Construction</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/"></a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/"></a>
                                </li>
                            </ul>
                        </div>
                        <!-- /.col-md-4  -->
                        <div class="col-md-3">
                            <ul class="nav flex-column">
                                <li class="nav-item">
                                    <div class="container section-title-column">
                                        <h3>
                                            <a class="nav-link active" href="/scarp/paift">OUTPUT</a>
                                        </h3>
                                    </div>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/scarp/paift/paift_trades_monitor/">Trades Monitor</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" href="/scarp/paift/paift_trades_attribution/">Trades Suspects</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!--  /.container  -->
            </div>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="#">Log Out</a>
        </li>
        </ul>
    </div>
    </nav>
</header>
"""