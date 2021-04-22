#!/bin/bash

# Credit:   https://unix.stackexchange.com/questions/413441/converting-numbers-into-full-written-words


digits=(
    "" one two three four five six seven eight nine
    ten eleven twelve thirteen fourteen fifteen sixteen seventeen eightteen nineteen
)
tens=("" "" twenty thirty forty fifty sixty seventy eighty ninety)
units=("" thousand million billion trillion)

number2words() {
    local -i number=$((10#$1))
    local -i u=0
    local words=()
    local group

    while ((number > 0)); do
        group=$(hundreds2words $((number % 1000)) )
        [[ -n "$group" ]] && group="$group ${units[u]}"

        words=("$group" "${words[@]}")

        ((u++))
        ((number = number / 1000))
    done
    echo "${words[*]}"
}

hundreds2words() {
    local -i num=$((10#$1))
    if ((num < 20)); then
        echo "${digits[num]}"
    elif ((num < 100)); then
        echo "${tens[num / 10]} ${digits[num % 10]}"
    else
        echo "${digits[num / 100]} hundred $("$FUNCNAME" $((num % 100)) )"
    fi
}

with_commas() {
    # sed -r ':a;s/^([0-9]+)([0-9]{3})/\1,\2/;ta' <<<"$1"
    # or, with just bash
    while [[ $1 =~ ^([0-9]+)([0-9]{3})(.*) ]]; do
        set -- "${BASH_REMATCH[1]},${BASH_REMATCH[2]}${BASH_REMATCH[3]}"
    done
    echo "$1"
}

for arg; do
    [[ $arg == *[^0-9]* ]] && result="NaN" || result=$(number2words "$arg")
    printf "%s\t%s\n" "$(with_commas "$arg")" "$result"
done

