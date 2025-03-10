auth_header_template = """
<header>
    <nav>
        <div class="logo">Hello,<b> {username} - {group} </b></div>
        <ul>
            <li><a href="/">Homepage</a></li>
            <li><a href="#who">About</a></li>
            <li class="dropdown">
                <a href="/" class="dropdown-toggle" data-toggle="dropdown">Services<span class="caret"></span></a>
                <div class="dropdown-content">
                    <div class="dropdown-content-paift">
                        <a href="/scarp/paift" class="dropdown-toggle">paift<span class="caret"></span></a>
                        <div class="dropdown-content-submenu">
                            <a href="/scarp/paift" class="dropdown">paift Input<span class="caret"></span></a>
                            <div class="dropdown-content-submenu">
                                <a href="/scarp/paift/preprocessing">paift Targets</a>
                            </div>
                            <a href="/scarp/paift/preprocessing">paift Preprocessing</a>
                            <a href="/scarp/paift/output">paift Output</a>
                        </div>
                    </div>
                </div>
            </li>
            <li><a href="#">Contact</a></li>
            <li><a href="/logout">Logout</a></li>
        </ul>
    </nav>
</header>
"""