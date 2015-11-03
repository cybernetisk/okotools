#!/bin/bash
#
# @author Henrik Steen

DIR_KREDITERINGER="../4 Krediteringer"
DIR_KONTOUTSKRIFTER="../4 Kontoutskrifter"
DIR_UTBETALINGER="../4 Utbetalinger"
DIR_UTSKRIFT="../TILUTSKRIFT"
DIR_INPUT="."

ISTEST=1
ISCOPY=1

# color definitions
RED='\033[1;31m'
GREEN='\033[1;32m'
GREEN2='\033[0;32m'
PURPLE='\033[1;35m'
YELLOW='\033[1;33m'
NC='\033[0m' # reset colors

echo "----------------------------------------"
echo "Cybernetisk Selskab banksortering-script"
echo "Laget av kasserer Henrik Steen"
echo "----------------------------------------"
echo

function q() {
	echo
	echo "Trykk enter for å avslutte"
	read line
	exit
}

function checkcount() {
	count=$(ls -1 *.pdf 2>/dev/null | wc -l)
	if [[ $count == 0 ]]; then
		echo "Fant ingen filer i mappa!"
		q
	fi

	echo "Fant $count PDF-filer til gjennomsyn"
}

function checkcopy() {
	echo
	echo "Skal filer kopieres til utskriftsmappe?"
	select opt in "Nei" "Ja (standard)"; do
		if [[ "$REPLY" == "1" ]]; then
			ISCOPY=0
		else
			ISCOPY=1
		fi
		break
	done
}

function checktest() {
	echo
	echo "Velg ønsket handling"
	select opt in "Kjør kun test (standard)" "Flytt filer"; do
		if [[ "$REPLY" == "2" ]]; then
			ISTEST=0
		else
			ISTEST=1
		fi
		break
	done
}

checkcount
checktest
checkcopy


function copytoprint() {
	if [[ $ISCOPY == "0" ]]; then
		return
	fi

	# bygg opp nytt filnavn og sjekk om denne finnes
	# hvis den finnes, finn et annet navn
	printname="$DIR_UTSKRIFT/$destname.pdf"

	local i=2
	while [[ -e "$printname" ]]; do
		printname="$destpath/$destname ($i).pdf"
		let i=i+1
	done

	if [[ $ISTEST == "1" ]]; then
		echo -e "${GREEN2}   $printname${NC}"
	else
		cp "$destfile" "$printname"
		echo -e "${GREEN2}   $printname${NC}"
	fi
}


function movetodest() {
	# bygg opp nytt filnavn og sjekk om denne finnes
	# hvis den finnes, finn et annet navn
	destfile="$destpath/$destname.pdf"

	local i=2
	exists=0
	while [[ -e "$destfile" ]]; do
		# sjekk om det er samme dokument
		s1=$(md5sum -b "$destfile" | awk '{ print $1 }')
		s2=$(md5sum -b "$filepath" | awk '{ print $1 }')
		if [[ "$s1" == "$s2" ]]; then
			echo -e "${RED}Filen '$x' eksisterer allerede som '$destfile'!${NC}"
			exists=1
			return
		fi

		destfile="$destpath/$destname ($i).pdf"
		let i=i+1
	done

	if [[ $ISTEST == "1" ]]; then
		echo -e "${GREEN}   $destfile${NC}"
	else
		mv "$filepath" "$destfile"
		echo -e "${GREEN}   $destfile${NC}"
	fi

	if [[ $exists == "0" ]]; then
		copytoprint
	fi
}

function extract_date_kreditering_normal() {
	date=""
	local x=0
	while true; do
		let n=56+$x
		line=$(echo "$filedata" | sed "${n}q;d")

		if [[ ! $line =~ ^[0-9]{2}/[0-9]{2}-[0-9]{4}$ ]]; then
			if (( x > 30 )); then
				return
			fi
			let x=$x+1
			continue
		fi

		date=${line:6:4}-${line:3:2}-${line:0:2}
		break
	done
}

function extract_date_kreditering_kid() {
	line=$(echo "$filedata" | grep -A1 "VAL.DATO" | tail -n 1)

	date=""
	if [[ $line =~ ^[0-9]{2}\.[0-9]{2}\.[0-9]{2}$ ]]; then
		date=20${line:6:2}-${line:3:2}-${line:0:2}
	fi
}

function fixdir() {
	if [[ ! -d "$destpath" ]]; then
		if [[ $ISTEST == "1" ]]; then
			echo -e "${PURPLE}   Mappen $destpath vil bli opprettet${NC}"
		else
			mkdir -p "$destpath"
			echo -e "${PURPLE}   Opprettet mappen $destpath${NC}"
		fi
	fi
}


function handlekreditering() {
	ISKID=0
	if [[ $filedata != *"Denne forsendelsen"* ]]; then
		ISKID=1
	fi

	# trekk ut dato fra filen
	if [[ $ISKID == "1" ]]; then
		extract_date_kreditering_kid
	else
		extract_date_kreditering_normal
	fi
	if [[ $date == "" ]]; then
		echo -e "${RED}   Klarte ikke å hente ut dato${NC}"
		return
	fi

	# trekk ut til-konto fra filen
	if [[ $ISKID == "1" ]]; then
		konto=$(echo "$filedata" | grep "KTO" | head -n 1 | sed 's/^.*\(\([0-9]\)\{4\}\) \(\([0-9]\)\{2\}\) \(\([0-9]\)\{5\}\).*$/\1.\3.\5/')
	else
		konto=$(echo "$filedata" | grep "konto" | head -n 1 | awk '{print $2}' | sed 's/[^0-9\.]//g')
	fi
	if [ "${#konto}" -ne "13" ]; then
		echo -e "${RED}   Fant ikke kontonr${NC}"
		return
	fi
	kortkonto=${konto:8}

	# kontroller at mappen for dennne filen finnes
	destpath="$DIR_KREDITERINGER/${date:0:4}/$konto"
	fixdir

	# flytt til ny mappe
	destname="Innbetalinger $kortkonto $date"
	movetodest
}

function handleutbetaling() {
	info=$(echo "$filedata" | sed '/^$/d')
	konto=$(echo "$info" | awk 'NR==8' | sed 's/.*\(....\) \(..\) \(.....\)$/\1.\2.\3/')
	kortkonto=$(echo "$info" | awk 'NR==8' | sed 's/.*\(.....\)$/\1/')
	mottaker=$(echo "$info" | awk 'NR==22' | sed 's/[^a-zA-Z0-9 \.,_-]/_/g')
	belop=$(echo "$info" | awk 'NR==23')
	dato=$(echo "$info" | awk 'NR==24' | awk 'BEGIN{FS=OFS="."}{print $3"-"$2"-"$1}')
	year=$(echo "$dato" | sed 's/^\(....\)-.*$/\1/')

	if [[ ${#year} -ne 4 ]]; then
		echo -e "${RED}   Klarte ikke å hente ut dato${NC}"
		return
	fi

	if [ "${#konto}" -ne "13" ]; then
		echo -e "${RED}   Fant ikke kontonr${NC}"
		return
	fi

	# kontroller at mappen for dennne filen finnes
	destpath="$DIR_UTBETALINGER/$year/$konto"
	fixdir

	# flytt til ny mappe
	destname="$dato $konto Betalt $mottaker ($belop)"
	movetodest
}

function handlekontoutskrift() {
	info=$(echo "$filedata" | sed '/^$/d')
	date=$(echo "$info" | head -n 1 | sed 's/^\(..\).\(..\).\(....\)$/\3-\2-\1/')

	if [ ${#date} -ne "10" ]; then
		echo -e "${RED}   Klarte ikke å hente ut dato${NC}"
		return
	fi

	nr=$(echo "$info" | grep -A 1 -m 1 'UTSKRIFTSNR.' | tail -n 1)
	re='^[0-9]+$'
	if ! [[ $nr =~ $re ]]; then
		echo -e "${RED}   Klarte ikke å hente ut utskriftsnummer${NC}"
		return
	fi

	konto=$(echo "$info" | grep -m 1 'KONTONR.' | sed 's/KONTONR\. //')
	re='^[0-9]{4}\.[0-9]{2}\.[0-9]{5}$'
	if ! [[ $konto =~ $re ]]; then
		echo -e "${RED}   Klarte ikke å hente ut kontonr${NC}"
		return
	fi

	if ! ls "$DIR_KONTOUTSKRIFTER/"*$konto* 1>/dev/null 2>&1; then
		echo -e "${RED}   Klarte ikke å identifisere mappen til kontoutskrift for konto $konto${NC}"
		return
	fi

	mappe=""
	for y in "$DIR_KONTOUTSKRIFTER/"*$konto*; do
		mappe=$y
	done

	destpath="$mappe"
	destname="Kontoutskrift ${konto:8:5} $date nr $nr"

	if [[ -e "$destpath/$destname.pdf" ]]; then
		echo -e "${RED}   Kontoutskrift eksisterer allerede som $destname${NC}"
		return
	fi

	movetodest
}


function checkfiles() {
	for filepath in "$DIR_INPUT/"*.pdf; do
		filedata=$(pdftotext "$filepath" - 2>/dev/null)

		echo -e "${YELLOW}Fil: $filepath${NC}"

		if [[ $filedata == *"MELDING OM KREDITERING"* ]]; then
			handlekreditering
		elif [[ $filedata == *"Godskrift på mottakers konto"* ]]; then
			handleutbetaling
		elif [[ $filedata == *"BETINGELSER PÅ KONTO"* ]]; then
			handlekontoutskrift
		else
			echo -e "${RED}   Ukjent fil: $filepath${NC}"
		fi
	done
}

echo
checkfiles

q
