"""
Country coordinates lookup
Maps country names to [latitude, longitude]
"""

COUNTRY_COORDINATES = {
    # North America
    'United States': [37.0902, -95.7129],
    'USA': [37.0902, -95.7129],
    'Canada': [56.1304, -106.3468],
    'Mexico': [23.6345, -102.5528],
    
    # Europe
    'United Kingdom': [55.3781, -3.4360],
    'UK': [55.3781, -3.4360],
    'France': [46.2276, 2.2137],
    'Germany': [51.1657, 10.4515],
    'Italy': [41.8719, 12.5674],
    'Spain': [40.4637, -3.7492],
    'Netherlands': [52.1326, 5.2913],
    'Belgium': [50.5039, 4.4699],
    'Switzerland': [46.8182, 8.2275],
    'Austria': [47.5162, 14.5501],
    'Poland': [51.9194, 19.1451],
    'Sweden': [60.1282, 18.6435],
    'Norway': [60.4720, 8.4689],
    'Denmark': [56.2639, 9.5018],
    'Finland': [61.9241, 25.7482],
    'Greece': [39.0742, 21.8243],
    'Portugal': [39.3999, -8.2245],
    'Ireland': [53.4129, -8.2439],
    'Russia': [61.5240, 105.3188],
    'Ukraine': [48.3794, 31.1656],
    'Romania': [45.9432, 24.9668],
    'Czech Republic': [49.8175, 15.4730],
    'Hungary': [47.1625, 19.5033],
    'Serbia': [44.0165, 21.0059],
    'Croatia': [45.1, 15.2],
    'Bulgaria': [42.7339, 25.4858],
    
    # Asia
    'China': [35.8617, 104.1954],
    'Japan': [36.2048, 138.2529],
    'India': [20.5937, 78.9629],
    'South Korea': [35.9078, 127.7669],
    'Thailand': [15.8700, 100.9925],
    'Vietnam': [14.0583, 108.2772],
    'Indonesia': [-0.7893, 113.9213],
    'Malaysia': [4.2105, 101.9758],
    'Singapore': [1.3521, 103.8198],
    'Philippines': [12.8797, 121.7740],
    'Pakistan': [30.3753, 69.3451],
    'Bangladesh': [23.6850, 90.3563],
    'Iran': [32.4279, 53.6880],
    'Iraq': [33.2232, 43.6793],
    'Israel': [31.0461, 34.8516],
    'Saudi Arabia': [23.8859, 45.0792],
    'UAE': [23.4241, 53.8478],
    'Turkey': [38.9637, 35.2433],
    'Afghanistan': [33.9391, 67.7100],
    'Myanmar': [21.9162, 95.9560],
    'Nepal': [28.3949, 84.1240],
    'Sri Lanka': [7.8731, 80.7718],
    
    # Africa
    'Egypt': [26.8206, 30.8025],
    'South Africa': [-30.5595, 22.9375],
    'Nigeria': [9.0820, 8.6753],
    'Kenya': [-0.0236, 37.9062],
    'Ethiopia': [9.1450, 40.4897],
    'Morocco': [31.7917, -7.0926],
    'Algeria': [28.0339, 1.6596],
    'Tunisia': [33.8869, 9.5375],
    'Ghana': [7.9465, -1.0232],
    'Tanzania': [-6.3690, 34.8888],
    'Uganda': [1.3733, 32.2903],
    'Zimbabwe': [-19.0154, 29.1549],
    'Sudan': [12.8628, 30.2176],
    'Libya': [26.3351, 17.2283],
    
    # South America
    'Brazil': [-14.2350, -51.9253],
    'Argentina': [-38.4161, -63.6167],
    'Chile': [-35.6751, -71.5430],
    'Colombia': [4.5709, -74.2973],
    'Peru': [-9.1900, -75.0152],
    'Venezuela': [6.4238, -66.5897],
    'Ecuador': [-1.8312, -78.1834],
    'Bolivia': [-16.2902, -63.5887],
    'Uruguay': [-32.5228, -55.7658],
    'Paraguay': [-23.4425, -58.4438],
    
    # Middle East
    'Syria': [34.8021, 38.9968],
    'Lebanon': [33.8547, 35.8623],
    'Jordan': [30.5852, 36.2384],
    'Yemen': [15.5527, 48.5164],
    'Oman': [21.4735, 55.9754],
    'Kuwait': [29.3117, 47.4818],
    'Qatar': [25.3548, 51.1839],
    'Bahrain': [26.0667, 50.5577],
    
    # Oceania
    'Australia': [-25.2744, 133.7751],
    'New Zealand': [-40.9006, 174.8860],
    'Papua New Guinea': [-6.3150, 143.9555],
    'Fiji': [-17.7134, 178.0650],
    
    # Central America & Caribbean
    'Guatemala': [15.7835, -90.2308],
    'Cuba': [21.5218, -77.7812],
    'Honduras': [15.2000, -86.2419],
    'Nicaragua': [12.8654, -85.2072],
    'Costa Rica': [9.7489, -83.7534],
    'Panama': [8.5380, -80.7821],
    'Jamaica': [18.1096, -77.2975],
    'Haiti': [18.9712, -72.2852],
    'Dominican Republic': [18.7357, -70.1627],
    
    # Eastern Europe
    'Belarus': [53.7098, 27.9534],
    'Lithuania': [55.1694, 23.8813],
    'Latvia': [56.8796, 24.6032],
    'Estonia': [58.5953, 25.0136],
    'Slovakia': [48.6690, 19.6990],
    'Slovenia': [46.1512, 14.9955],
    'Moldova': [47.4116, 28.3699],
    'Albania': [41.1533, 20.1683],
    'North Macedonia': [41.6086, 21.7453],
    'Bosnia': [43.9159, 17.6791],
    'Montenegro': [42.7087, 19.3744],
    
    # Central Asia
    'Kazakhstan': [48.0196, 66.9237],
    'Uzbekistan': [41.3775, 64.5853],
    'Turkmenistan': [38.9697, 59.5563],
    'Kyrgyzstan': [41.2044, 74.7661],
    'Tajikistan': [38.8610, 71.2761],
    'Mongolia': [46.8625, 103.8467],
    
    # Additional Asian Countries
    'Cambodia': [12.5657, 104.9910],
    'Laos': [19.8563, 102.4955],
    'Bhutan': [27.5142, 90.4336],
    'Maldives': [3.2028, 73.2207],
    'Brunei': [4.5353, 114.7277],
    'Taiwan': [23.6978, 120.9605],
    'Hong Kong': [22.3193, 114.1694],
    'Macau': [22.1987, 113.5439],
    
    # Additional African Countries
    'Senegal': [14.4974, -14.4524],
    'Ivory Coast': [7.5400, -5.5471],
    'Cameroon': [7.3697, 12.3547],
    'Congo': [-4.0383, 21.7587],
    'Angola': [-11.2027, 17.8739],
    'Mozambique': [-18.6657, 35.5296],
    'Madagascar': [-18.7669, 46.8691],
    'Namibia': [-22.9576, 18.4904],
    'Botswana': [-22.3285, 24.6849],
    'Zambia': [-13.1339, 27.8493],
    'Malawi': [-13.2543, 34.3015],
    'Rwanda': [-1.9403, 29.8739],
    'Burundi': [-3.3731, 29.9189],
    'Somalia': [5.1521, 46.1996],
    'Eritrea': [15.1794, 39.7823],
    'Djibouti': [11.8251, 42.5903],
    'Mali': [17.5707, -3.9962],
    'Niger': [17.6078, 8.0817],
    'Chad': [15.4542, 18.7322],
    'Mauritania': [21.0079, -10.9408],
    'Benin': [9.3077, 2.3158],
    'Togo': [8.6195, 0.8248],
    'Sierra Leone': [8.4606, -11.7799],
    'Liberia': [6.4281, -9.4295],
    'Guinea': [9.9456, -9.6966],
    'Burkina Faso': [12.2383, -1.5616],
    'Gabon': [-0.8037, 11.6094],
    'Equatorial Guinea': [1.6508, 10.2679],
    'Central African Republic': [6.6111, 20.9394],
    
    # Pacific Islands
    'Solomon Islands': [-9.6457, 160.1562],
    'Vanuatu': [-15.3767, 166.9592],
    'Samoa': [-13.7590, -172.1046],
    'Tonga': [-21.1789, -175.1982],
    'Kiribati': [-3.3704, -168.7340],
    'Micronesia': [7.4256, 150.5508],
    'Palau': [7.5150, 134.5825],
}


def get_coordinates(country):
    """
    Get coordinates for a country name
    
    Args:
        country (str): Country name
        
    Returns:
        list: [latitude, longitude] or [0, 0] if not found
    """
    # Try exact match
    if country in COUNTRY_COORDINATES:
        return COUNTRY_COORDINATES[country]
    
    # Try case-insensitive match
    country_lower = country.lower()
    for key, coords in COUNTRY_COORDINATES.items():
        if key.lower() == country_lower:
            return coords
    
    # Default to [0, 0] if not found
    return [0, 0]


def get_all_countries():
    """Get list of all supported countries"""
    return list(COUNTRY_COORDINATES.keys())
