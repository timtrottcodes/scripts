<#
.SYNOPSIS
    Retrieves all items associated with each person from an Emby server for a specified user.

.DESCRIPTION
    This script connects to an Emby server using the REST API, retrieves all "Persons" 
    (actors, directors, etc.), and then fetches all items linked to each person for 
    a specific user. Results can be further processed or stored as needed.

.PARAMETER $apiKey
    Your Emby server API key for authentication.

.PARAMETER $serverUrl
    The base URL of your Emby server (e.g., http://192.168.1.200:8096).

.PARAMETER $userId
    The ID of the user whose items you want to query.

.EXAMPLE
    PS> .\EmbyPersonItems.ps1
    Retrieves all media items associated with all persons from the specified Emby server 
    for the given user.

.NOTES
    - Requires PowerShell and network access to the Emby server.
    - Results are returned as PowerShell objects for easy manipulation.
#>

# -----------------------------
# Configurable variables
# -----------------------------
$apiKey = "f4a527d5821a46a9b6ea21d0d5aebf5b"
$serverUrl = "http://192.168.1.200:8096"
$userId = "42cc6ea1f5074515b8319e802347b159"

# -----------------------------
# Fetch all persons from the server
# -----------------------------
$persons = Invoke-RestMethod -Uri "$serverUrl/emby/Persons?api_key=$apiKey"

# -----------------------------
# Fetch items for each person for the specified user
# -----------------------------
$persons.Items | ForEach-Object {
    $personId = $_.Id
    $items = Invoke-RestMethod -Uri "$serverUrl/Users/$userId/Items/$personId?api_key=$apiKey"
    
    # Output the items (can be further processed or exported)
    $items
}