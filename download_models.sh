#! /bin/bash

mkdir -p models

while [[ $# -gt 0 ]]
do
    key="${1}"
    case ${key} in
    inception)
        INPUTPARAM="${2}"
        shift # past argument
        shift # past value
        ;;
    mobilenet)
        OUTPUTPARAM="${2}"
        shift # past argument
        shift # past value
        ;;
    resnet)
        echo "Show help"
        shift # past argument
        ;;
    *)    # unknown option
        shift # past argument
        ;;
    esac
    shift
done
