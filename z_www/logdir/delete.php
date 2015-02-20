<?php
//echo file_get_contents(glob("tmp*")[0]);
foreach (glob("tmp*") as $file) {
	 unlink($file);
}
