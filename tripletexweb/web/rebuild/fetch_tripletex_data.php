<?php

$result = shell_exec('bash -c \'export LANG=nb_NO.UTF-8; cd ../../../tripletex && source env/bin/activate && ./fetch_tripletex_data.py\' 2>&1');

echo '<p><a href="..">Gå tilbake</a></p>
<p>Resultat av operasjonen:</p>
<pre>'.htmlspecialchars($result).'</pre>';
