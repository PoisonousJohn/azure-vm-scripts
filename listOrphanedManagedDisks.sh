#!/bin/bash
az disk list --query "[?managedBy==null]" -o tsv
