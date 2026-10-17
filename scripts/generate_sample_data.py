"""
CRADLE Multi-City Sample Data Generator
Generates realistic, development-ready spatial datasets for:
1. Chennai (Tamil Nadu) - 200 GCC Wards across 15 Zones
2. Coimbatore (Tamil Nadu) - 100 CCMC Wards across 5 Zones
3. Bengaluru (Karnataka) - 198 BBMP Wards across 8 Zones
4. Hyderabad (Telangana) - 150 GHMC Wards across 6 Zones
5. Delhi (National Capital Territory) - 250 MCD Wards across 12 Zones

Every ward is assigned an authentic, recognized locality/neighborhood name.
All outputs enforce uniform composite geographic schemas and are designated
as SYNTHETIC DEVELOPMENT DATA with complete data provenance tags.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point, box
from shapely.ops import voronoi_diagram

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# City-specific real landmark hospitals for calibration
LANDMARK_FACILITIES = {
    "chennai": [
        ("Rajiv Gandhi Government General Hospital", 13.0805, 80.2785, "General Hospital", 1200, 150, "Public"),
        ("Government Stanley Medical College Hospital", 13.1090, 80.2870, "General Hospital", 1000, 120, "Public"),
        ("Government Kilpauk Medical College Hospital", 13.0785, 80.2415, "General Hospital", 750, 95, "Public"),
        ("Government Royapettah Hospital", 13.0535, 80.2605, "Government Hospital", 550, 70, "Public"),
        ("Tambaram Sanatorium Government Hospital", 12.9340, 80.1380, "Government Hospital", 300, 45, "Public"),
        ("Apollo Hospitals Main, Greams Road", 13.0605, 80.2525, "Multi-Speciality Hospital", 550, 90, "Private"),
        ("MIOT International, Manapakkam", 13.0180, 80.1780, "Multi-Speciality Hospital", 500, 80, "Private"),
        ("SIMS Hospital, Vadapalani", 13.0510, 80.2110, "Multi-Speciality Hospital", 345, 60, "Private"),
        ("Fortis Malar Hospital, Adyar", 13.0030, 80.2610, "Multi-Speciality Hospital", 220, 45, "Private"),
        ("Kauvery Hospital, Alwarpet", 13.0370, 80.2510, "Multi-Speciality Hospital", 250, 45, "Private"),
    ],
    "coimbatore": [
        ("Coimbatore Medical College Hospital (CMCH)", 11.0025, 76.9675, "General Hospital", 1050, 130, "Public"),
        ("ESI Medical College Hospital, Singanallur", 11.0080, 77.0180, "Government Hospital", 500, 65, "Public"),
        ("PSG Hospitals, Peelamedu", 11.0250, 77.0050, "Multi-Speciality Hospital", 650, 90, "Private"),
        ("Ganga Hospital, Ram Nagar", 11.0180, 76.9580, "Multi-Speciality Hospital", 450, 70, "Private"),
        ("Kovai Medical Center and Hospital (KMCH)", 11.0550, 77.0420, "Multi-Speciality Hospital", 800, 110, "Private"),
        ("Sri Ramakrishna Hospital, Awarampalayam", 11.0220, 76.9850, "Multi-Speciality Hospital", 550, 75, "Private"),
        ("G. Kuppuswamy Naidu Memorial Hospital (GKNM)", 11.0120, 76.9800, "Multi-Speciality Hospital", 400, 60, "Private"),
        ("Government District Headquarter Hospital, Pollachi Rd", 10.9850, 76.9550, "Government Hospital", 250, 35, "Public"),
    ],
    "bengaluru": [
        ("Victoria Hospital (BMCRI)", 12.9630, 77.5740, "General Hospital", 1150, 140, "Public"),
        ("Bowring and Lady Curzon Hospital", 12.9830, 77.6050, "General Hospital", 700, 85, "Public"),
        ("KC General Hospital, Malleshwaram", 12.9980, 77.5700, "Government Hospital", 450, 55, "Public"),
        ("Jayanagar General Hospital", 12.9280, 77.5850, "Government Hospital", 350, 45, "Public"),
        ("NIMHANS Neuro-Psychiatric Centre", 12.9400, 77.5950, "General Hospital", 800, 120, "Public"),
        ("Manipal Hospital, Old Airport Road", 12.9580, 77.6480, "Multi-Speciality Hospital", 600, 95, "Private"),
        ("Narayana Institute of Cardiac Sciences", 12.8250, 77.6900, "Multi-Speciality Hospital", 750, 100, "Private"),
        ("Aster CMI Hospital, Hebbal", 13.0550, 77.5920, "Multi-Speciality Hospital", 500, 80, "Private"),
        ("Apollo Hospital, Bannerghatta Road", 12.8950, 77.5980, "Multi-Speciality Hospital", 450, 75, "Private"),
        ("Fortis Hospital, Cunningham Road", 12.9890, 77.5950, "Multi-Speciality Hospital", 350, 60, "Private"),
    ],
    "hyderabad": [
        ("Osmania General Hospital, Afzal Gunj", 17.3780, 78.4750, "General Hospital", 1168, 145, "Public"),
        ("Gandhi Hospital, Musheerabad", 17.4240, 78.5020, "General Hospital", 1000, 130, "Public"),
        ("Nizam's Institute of Medical Sciences (NIMS), Punjagutta", 17.4220, 78.4520, "General Hospital", 900, 115, "Public"),
        ("Government Area Hospital, King Koti", 17.3910, 78.4850, "Government Hospital", 350, 45, "Public"),
        ("Government Area Hospital, Malakpet", 17.3720, 78.5050, "Government Hospital", 250, 35, "Public"),
        ("Apollo Hospitals, Jubilee Hills", 17.4150, 78.4120, "Multi-Speciality Hospital", 550, 90, "Private"),
        ("Yashoda Hospital, Secunderabad", 17.4420, 78.5010, "Multi-Speciality Hospital", 450, 75, "Private"),
        ("CARE Hospitals, Banjara Hills", 17.4180, 78.4480, "Multi-Speciality Hospital", 435, 70, "Private"),
        ("KIMS Hospitals, Secunderabad", 17.4380, 78.4900, "Multi-Speciality Hospital", 500, 80, "Private"),
        ("AIG Hospitals, Gachibowli", 17.4410, 78.3620, "Multi-Speciality Hospital", 800, 110, "Private"),
    ],
    "delhi": [
        ("All India Institute of Medical Sciences (AIIMS)", 28.5672, 77.2100, "General Hospital", 2400, 300, "Public"),
        ("Safdarjung Hospital & Vardhman Mahavir Medical College", 28.5695, 77.2075, "General Hospital", 1800, 220, "Public"),
        ("Dr. Ram Manohar Lohia (RML) Hospital", 28.6255, 77.2015, "General Hospital", 1200, 160, "Public"),
        ("Lok Nayak Jai Prakash Narayan (LNJP) Hospital", 28.6365, 77.2415, "General Hospital", 2000, 240, "Public"),
        ("Guru Teg Bahadur (GTB) Hospital, Dilshad Garden", 28.6830, 77.3110, "General Hospital", 1500, 180, "Public"),
        ("Sir Ganga Ram Hospital, Rajinder Nagar", 28.6385, 77.1895, "Multi-Speciality Hospital", 675, 120, "Private"),
        ("Max Super Speciality Hospital, Saket", 28.5280, 77.2120, "Multi-Speciality Hospital", 550, 95, "Private"),
        ("Indraprastha Apollo Hospitals, Sarita Vihar", 28.5410, 77.2830, "Multi-Speciality Hospital", 710, 110, "Private"),
        ("Fortis Escorts Heart Institute, Okhla", 28.5605, 77.2755, "Multi-Speciality Hospital", 310, 65, "Private"),
        ("Rajiv Gandhi Super Speciality Hospital, Tahirpur", 28.6890, 77.3190, "General Hospital", 650, 90, "Public"),
        ("Deen Dayal Upadhyay Hospital, Hari Nagar", 28.6270, 77.1120, "Government Hospital", 640, 85, "Public"),
        ("BLK-Max Super Speciality Hospital, Pusa Road", 28.6440, 77.1800, "Multi-Speciality Hospital", 650, 100, "Private"),
    ],
}


# City-specific authentic ward & neighborhood names organized by Zone ID
CITY_WARD_NAMES = {
    "chennai": {
        1: ["Kathivakkam", "Ernavoor", "Wimco Nagar", "Ennore Port", "Thiruvottiyur West", "Sathangadu", "Mattankuppam", "Kaladipet", "Tollgate North", "Rajakadai", "Shanmugapuram", "Ellaiamman Koil", "Jothi Nagar", "Tiruvottiyur Market"],
        2: ["Edayanchavadi", "Sadayankuppam", "Kadapakkam", "Manali New Town", "Kosappur", "Mathur MMDA", "Chinna Sekkadu"],
        3: ["Puzhal Lake", "Surapet", "Puthagaram", "Kathirvedu", "Madhavaram Central", "Moolakadai", "Kodungaiyur West", "Kannadasan Nagar", "Muthamizh Nagar", "Erukkanchery", "Kaviarasu Nagar", "Thattankulam"],
        4: ["Kodungaiyur East", "Korukkupet", "Tondiarpet Market", "Washermanpet North", "Kasimedu Harbour", "Royapuram Railway Colony", "Stanley Enclave", "Old Washermanpet", "Meenambal Nagar", "Bojaraja Nagar", "Grace Garden", "Sanjeevi Rayan Koil", "Motilal Nagar", "Seniamman Koil", "Basin Bridge"],
        5: ["George Town North", "Broadway Commercial", "Park Town", "Sowcarpet Central", "Kondithope", "Elephant Gate", "Muthialpet", "Vallal Seethakathi", "Harbour Port", "Choolai North", "Periamet", "Vepery Central", "Ripon Building Area", "Nehru Stadium Area", "Madras Central"],
        6: ["Kolathur East", "Kolathur West", "Perambur North", "Perambur South", "Sembium", "Siruvallur", "Agaram", "Thiru Vi Ka Nagar", "Ayanavaram East", "Ayanavaram West", "Otteri", "Pattalam", "Pulianthope", "Strahans Road", "Choolai South"],
        7: ["Padi Junction", "Mogappair East", "Mogappair West", "Ambattur Industrial Estate", "Mannurpet", "Korattur North", "Korattur South", "Pattaravakkam", "Ambattur OT", "Menambedu", "Oragadam Ambattur", "Venkatapuram", "Kallikuppam", "Surapet Road", "TI Cycles Enclave"],
        8: ["Anna Nagar East", "Anna Nagar West", "Anna Nagar Western Extn", "Shenoy Nagar", "Aminjikarai", "Kilpauk North", "Kilpauk Garden", "Chetpet East", "Chetpet West", "Shanthi Colony", "Thirumangalam", "Villivakkam North", "Villivakkam South", "ICF Colony", "Nathamuni"],
        9: ["Nungambakkam High Rd", "Thousand Lights East", "Thousand Lights West", "Gopalapuram", "Royapettah", "Triplicane North", "Marina Beach Enclave", "Chepauk Stadium", "Ice House", "Mirsahibpet", "Alwarpet North", "Alwarpet South", "Teynampet Central", "Poes Garden", "DMS Enclave", "Venus Colony", "Eldams Road", "Seethammal Colony"],
        10: ["Kodambakkam North", "Kodambakkam South", "Vadapalani Temple", "Vadapalani Central", "Ashok Nagar North", "Ashok Nagar South", "West Mambalam", "T. Nagar Panagal Park", "Pondy Bazaar", "CIT Nagar", "Saidapet North", "Saidapet West", "KK Nagar West", "KK Nagar East", "Nesapakkam", "MGR Nagar"],
        11: ["Valasaravakkam Central", "Alwarthirunagar", "Porur East", "Porur Lake", "Karambakkam", "Maduravoyal North", "Maduravoyal South", "Nerkundram", "Chinmaya Nagar", "Virugambakkam North", "Virugambakkam South", "Saligramam", "Ramapuram"],
        12: ["Alandur Court", "St. Thomas Mount", "Guindy Industrial Estate", "Ekkatuthangal", "Nandambakkam", "Meenambakkam Airport", "Pazhavanthangal", "Nanganallur North", "Nanganallur South", "Moovarasanpet", "Madipakkam West", "Adambakkam"],
        13: ["Guindy Race Course", "Raj Bhavan Enclave", "IIT Madras Enclave", "Gandhi Nagar Adyar", "Kasturba Nagar", "Indira Nagar Adyar", "Besant Nagar Beach", "Kalakshetra Colony", "Thiruvanmiyur North", "Thiruvanmiyur South", "Kotturpuram", "Velachery West", "Velachery East"],
        14: ["Perungudi OMR", "Kandanchavadi", "Thoraipakkam North", "Thoraipakkam South", "Pallikaranai Marsh", "Pallikaranai Central", "Madipakkam East", "Puzhuthivakkam", "Ullagaram", "Kovilambakkam", "Veerangal Odai"],
        15: ["Sholinganallur IT Hub", "Karapakkam OMR", "Injambakkam ECR", "Akkarai Beach", "Neelankarai", "Palavakkam", "Semmancheri", "Uthandi", "Navalur Border"],
    },
    "coimbatore": {
        1: ["Singanallur North", "Singanallur South", "Ramanathapuram East", "Ramanathapuram Central", "Ondipudur", "Varadharajapuram", "Neelikonampalayam", "Masakalipalayam", "Sowripalayam", "Udayampalayam", "Meena Estate", "Kallimadai", "Nanjundapuram East", "Trichy Road", "SIHS Colony", "Civil Aerodrome", "SITRA Enclave", "Hope College", "Peelamedu East", "PSG Tech Enclave"],
        2: ["RS Puram West", "RS Puram East", "DB Road", "Saibaba Colony North", "Saibaba Colony South", "Vadavalli East", "Vadavalli West", "Veerakeralam", "Telungupalayam", "Selvapuram North", "Selvapuram South", "Kumarasamy Lake", "Thondamuthur Road", "Sukrawarpet", "Flower Market", "Gandhi Park", "Koundampalayam West", "Edayarpalayam", "TVS Nagar", "Mullai Nagar"],
        3: ["Ganapathy West", "Ganapathy East", "Ganapathy Maanagar", "Gandhipuram Central", "Cross Cut Road", "Ram Nagar", "Sivananda Colony", "Tatabad", "HUDCO Colony", "Rathinapuri", "Sanganoor", "Thudiyalur", "Saravanampatti IT Park", "Chinnavedampatti", "Vellakinar", "Urumandampalayam", "Cheran Ma Nagar", "Vilankurichi", "Peelamedu Pudur", "Krishnarayapuram"],
        4: ["Ukkadam North", "Ukkadam Periyakulam", "Podanur Junction", "Podanur East", "Kurichi North", "Kurichi South", "Sundarapuram", "SIDCO Industrial Estate", "Eachanari", "Kuniyamuthur North", "Kuniyamuthur South", "Kovaipudur Phase I", "Kovaipudur Phase II", "Perur Temple", "Perur Chettipalayam", "Madukkarai Road", "Aathupalam", "Karumbukadai", "Saramedu", "Al-Ameen Colony"],
        5: ["Town Hall", "Big Bazaar Street", "Oppanakara Street", "Railway Station Enclave", "Race Course North", "Race Course South", "VOC Park", "Gopalapuram Coimbatore", "Red Fields", "Puliyakulam Central", "Puliyakulam South", "Ramanathapuram West", "Siddhapudur", "Awarampalayam", "Papanaickenpalayam", "Mani High School Area", "CMCH Hospital Area", "Brooke Bond Road", "Sukrawarpet North", "Valankulam Lake"],
    },
    "bengaluru": {
        1: ["Indiranagar HAL 2nd Stage", "Indiranagar Defence Colony", "Domlur", "Ulsoor Lake", "Shivajinagar Commercial St", "Frazer Town (Pulakeshinagar)", "Cox Town", "Cooke Town", "Benson Town", "Richard's Town", "Lingarajapuram", "Kammanahalli", "Banaswadi ORR", "HRBR Layout", "Kalyan Nagar", "HBR Layout 1st Block", "HBR Layout 2nd Block", "Hennur Road", "Kacharakanahalli", "Jeevanbheemanagar", "Jogupalya", "Shanthala Nagar (Brigade Rd)", "Sampangiram Nagar", "Neelasandra", "Austin Town"],
        2: ["Malleshwaram 8th Cross", "Malleshwaram 18th Cross", "Vyalikaval", "Sadashivanagar", "Rajajinagar 1st Block", "Rajajinagar 3rd Block", "Rajajinagar 6th Block", "Basaveshwaranagar", "Mahalakshmi Layout", "Subramanya Nagar", "Prakash Nagar", "Gayathri Nagar", "Dayananda Nagar", "Bhashyam Nagar", "Sriram Mandir", "Shivanagar", "Govindraj Nagar", "Kamakshipalya", "Kaveripura", "Vijayanagar Club Road", "RPC Layout", "Hampi Nagar", "Agrahara Dasarahalli", "Tollgate Vijayanagar", "Magadi Road"],
        3: ["Jayanagar 4th Block", "Jayanagar 7th Block", "Jayanagar 9th Block", "Basavanagudi Gandhi Bazaar", "Bull Temple Road", "Shankarapuram", "Chamrajpet North", "Chamrajpet South", "VV Puram Food Street", "Srinagar Bengaluru", "Hanumanth Nagar", "Girinagar", "Banashankari 1st Stage", "Banashankari 2nd Stage", "Banashankari 3rd Stage", "Padmanabhanagar", "Kumaraswamy Layout", "ISRO Layout", "Uttarahalli", "Yediyur Lake", "Siddapura South", "Pattabhirama Nagar", "Byrasandra", "Madhavan Park", "South End Circle"],
        4: ["Koramangala 3rd Block", "Koramangala 5th Block", "Koramangala 7th Block", "Koramangala 8th Block", "HSR Layout Sector 1", "HSR Layout Sector 2", "HSR Layout Sector 3", "HSR Layout Sector 4", "HSR Layout Sector 6", "HSR Layout Sector 7", "BTM Layout 1st Stage", "BTM Layout 2nd Stage", "Madiwala Lake", "Tavarekere", "Silk Board Enclave", "Bommanahalli Central", "Hongasandra", "Begur Road", "Bilekahalli", "Arekere MICO Layout", "Hulimavu Gate", "Gottigere", "Konanakunte Cross", "Anjanapura", "Singasandra"],
        5: ["Peenya Industrial Area 1st Phase", "Peenya 2nd Phase", "Peenya 3rd Phase", "T. Dasarahalli", "Jalahalli West", "Jalahalli Cross", "Chokkasandra", "Bagalgunte", "MEI Colony", "Shettihalli", "Mallasandra", "Abbigere", "HMT Layout Dasarahalli", "Ravindra Nagar", "Nelagadaranahalli", "Prashanth Nagar", "Sidedahalli", "Soundarya Layout", "Karihobanahalli", "Thigalarapalya", "Andrahalli", "D-Group Layout", "Doddagollarahatti", "Peenya Plantation", "Gangondanahalli Dasarahalli"],
        6: ["Whitefield Inner Circle", "Whitefield ECC Road", "ITPL Main Road", "Kadugodi", "Hope Farm Junction", "Hoodi Junction", "Brookefield", "Kundalahalli Gate", "Marathahalli Bridge", "Marathahalli Colony", "Bellandur ORR", "Bellandur Lake", "Devarabisanahalli SEZ", "Kadubeesanahalli", "Varthur Lake", "Panathur", "Doddanekkundi Industrial", "Mahadevapura Ring Rd", "KR Puram Market", "KR Puram Lake", "Ramamurthy Nagar", "TC Palya", "Horamavu Agara", "Kasavanahalli", "Doddakannelli"],
        7: ["RR Nagar Ideal Homes", "RR Nagar BEML Layout", "RR Nagar Temple Ward", "Kengeri Satellite Town", "Kengeri Upanagara", "Nagarbhavi 1st Stage", "Nagarbhavi 2nd Stage", "Nayandahalli Junction", "Chandra Layout", "Gangondanahalli RR", "Deepanjali Nagar", "Avalahalli", "Muneshwara Block", "Byatarayanapura Mysore Rd", "Gnanabharathi Bangalore Univ", "Ullal Upanagar", "Malathahalli", "Hemmigepura", "Banashankari 6th Stage", "Channasandra RR", "Kumbalgodu Border", "Kengeri Gollahalli", "Doddabele", "Mailasandra"],
        8: ["Yelahanka Old Town", "Yelahanka New Town 4th Phase", "Yelahanka New Town 1st Phase", "Kogilu Cross", "Jakkur Flying Club", "Jakkur Aerodrome Ward", "Hebbal Flyover Enclave", "Hebbal Kempapura", "Bellary Road", "RT Nagar Post Office", "RT Nagar Police Station", "Ganganagar", "Dinnur", "Vidyaranyapura Central", "Vidyaranyapura NTI Layout", "Doddaballapur Road", "Sahakarnagar North", "Sahakarnagar South", "Kodigehalli", "Byatarayanapura Bellary Rd", "Thanisandra Main Road", "Manyata Tech Park Enclave", "Nagawara Junction", "Hegde Nagar"],
    },
    "hyderabad": {
        1: ["Charminar Historic Core", "Laad Bazaar", "Chowmahalla Palace", "Afzal Gunj", "Salar Jung Museum", "High Court Enclave", "Ghansi Bazaar", "Moghalpura", "Shah Ali Banda", "Falaknuma Palace", "Chandrayangutta", "Uppuguda", "Jangammet", "Barkas", "Riyasat Nagar", "Rein Bazaar", "Yakutpura North", "Yakutpura South", "Dabirpura", "Chanchalguda", "Madannapet", "Santosh Nagar", "IS Sadan", "Saidabad", "Edi Bazaar"],
        2: ["Banjara Hills Road No 1", "Banjara Hills Road No 12", "Jubilee Hills Checkpost", "Jubilee Hills Road No 36", "Film Nagar", "Somajiguda", "Raj Bhavan Road", "Punjagutta Circle", "Ameerpet Cross Roads", "SR Nagar", "Sanjeeva Reddy Nagar", "Balkampet", "Begumpet Airport Area", "Prakash Nagar Begumpet", "Kundanbagh", "Khairatabad Junction", "Anandnagar Khairatabad", "Lakdikapul", "Red Hills Hyderabad", "Nampally Station", "Abids GPO", "Gunfoundry", "Basheerbagh", "Himayatnagar", "Narayanaguda"],
        3: ["Secunderabad Station", "Paradise Circle", "Clock Tower Secunderabad", "MG Road Secunderabad", "Rashtrapati Road", "Marredpally West", "Marredpally East", "Karkhana", "Gunrock Enclave", "Bowenpally Old", "Bowenpally New", "Trimulgherry", "Bolarum Bazaar", "Alwal Hills", "Old Alwal", "Lothkunta", "Malkajgiri Central", "Anandbagh", "Safilguda Lake", "Neredmet Cross Road", "Moula Ali Kaman", "ECIL Cross Roads", "AS Rao Nagar", "Sainikpuri", "Kapra Lake"],
        4: ["Hitec City Cyber Towers", "Madhapur Mindspace", "Gachibowli Financial District", "Gachibowli Stadium", "Kondapur RTO", "Kothaguda Junction", "Hafeezpet", "Miyapur Metro Station", "Miyapur Allwyn Colony", "Chanda Nagar", "Gangaram", "Lingampally Station", "BHEL Township", "Serilingampally Town", "Nanakramguda SEZ", "Rai Durgam", "Manikonda Jagir", "Puppalguda", "Khajaguda", "Botanical Garden Ward", "Shilparamam Arts Village", "Telecom Nagar", "Madhava Reddy Colony", "Gulmohar Park Serilingampally", "Tellapur Road"],
        5: ["KPHB Phase 1", "KPHB Phase 4", "KPHB Phase 7", "Kukatpally Main Road", "Vivekanandanagar Kukatpally", "Balanagar Industrial Area", "Ferozguda", "Fathenagar", "Moosapet Metro", "Bharat Nagar", "Erragadda", "Sanathnagar Industrial", "Borabanda Bus Stand", "Allapur", "Motinagar", "IDPL Colony", "Jagathgirigutta", "Rodamistry Nagar", "Shapur Nagar", "Jeedimetla Phase 1", "Jeedimetla Phase 3", "Gajularamaram", "Pragathi Nagar", "Nizampet Village", "Bachupally"],
        6: ["LB Nagar Ring Road", "Kothapet Fruit Market", "Chaitanyapuri", "Dilsukhnagar Main Rd", "Gaddiannaram", "Saroornagar Lake", "Saroornagar Central", "Kothapet HUDA Complex", "Mansoorabad", "Auto Nagar Industrial", "Vanasthalipuram Red Tank", "Vanasthalipuram Complex", "NGO Colony LB Nagar", "Hastinapuram", "Karmanghat Temple", "Champapet", "Lingojiguda", "BN Reddy Nagar", "Meerpet", "Badangpet", "Uppal Ring Road", "Ramanthapur TV Studio", "Habsiguda Metro", "Nacharam Industrial", "Mallapur"],
    },
    "delhi": {
        1: ["Connaught Place", "Janpath", "Shivaji Stadium Enclave", "Barakhamba Road", "Mandi House", "Pragati Maidan", "India Gate Enclave", "Khan Market", "Lodhi Colony", "Lodhi Estate", "Defence Colony Flyover", "Defence Colony Main", "South Extension Part 1", "South Extension Part 2", "Kotla Mubarakpur", "Sewa Nagar", "Andrews Ganj", "Lajpat Nagar 1", "Lajpat Nagar 2", "Lajpat Nagar 3", "Lajpat Nagar 4"],
        2: ["Greater Kailash 1", "Greater Kailash 2", "CR Park (Chittaranjan Park)", "Kalkaji Main", "Govindpuri Metro", "Alaknanda", "Hauz Khas Village", "Hauz Khas Enclave", "Green Park Main", "Green Park Extension", "Safdarjung Enclave", "Safdarjung Development Area", "Malviya Nagar Corner", "Malviya Nagar Market", "Saket District Centre", "Saket J-Block", "Pushp Vihar Sector 1", "Pushp Vihar Sector 4", "Mehrauli Qutub Minar", "Vasant Vihar", "Vasant Kunj Sector A"],
        3: ["Rajouri Garden Market", "Rajouri Garden Extension", "Tagore Garden", "Subhash Nagar", "Tilak Nagar Central", "Tilak Nagar East", "Janakpuri Block A", "Janakpuri Block B", "Janakpuri Block C", "Janakpuri District Centre", "Vikas Puri Block F", "Vikas Puri Block H", "Uttam Nagar East", "Uttam Nagar West", "Mohan Garden", "Nawada Metro", "Bindapur", "Matiala West", "Paschim Vihar East", "Paschim Vihar West", "Punjabi Bagh West"],
        4: ["Dwarka Sector 6", "Dwarka Sector 10 Metro", "Dwarka Sector 12", "Dwarka Sector 21 Junction", "Dwarka Sector 23", "Palam Village", "Palam Extension", "Sadh Nagar", "Mahavir Enclave", "Nasirpur", "Manglapuri", "Sagarpur West", "Sagarpur East", "Najafgarh Market", "Najafgarh Thana", "Dichaon Kalan", "Roshanpura", "Chhawla", "Kakrola", "Matiala Extension", "Kapashera Border"],
        5: ["Rohini Sector 3", "Rohini Sector 7", "Rohini Sector 8", "Rohini Sector 9", "Rohini Sector 11", "Rohini Sector 15", "Rohini Sector 16", "Rohini Sector 18", "Rohini Sector 21", "Rohini Sector 24", "Pitampura TV Tower", "Pitampura Kohat Enclave", "Pitampura Madhuban Chowk", "Rani Bagh Market", "Saraswati Vihar", "Prashant Vihar", "Mangolpuri Block A", "Mangolpuri Block D", "Mangolpuri Industrial", "Sultanpuri Block C", "Sultanpuri Block P"],
        6: ["Civil Lines Metro", "Delhi University North Campus", "Mall Road Civil Lines", "Timarpur", "Mukherjee Nagar Central", "Mukherjee Nagar Batra", "Model Town 1", "Model Town 2", "Model Town 3", "Gujranwala Town", "Derawal Nagar", "GTB Nagar Metro", "Kingsway Camp", "Hudson Lane", "Kamla Nagar Market", "Roop Nagar", "Shakti Nagar", "Vijay Nagar", "Azadpur Mandi", "Jahangirpuri Block A", "Jahangirpuri Block EE"],
        7: ["Karol Bagh Ajmal Khan Rd", "Karol Bagh Arya Samaj", "Rajinder Nagar New", "Old Rajinder Nagar", "Patel Nagar East", "Patel Nagar West", "South Patel Nagar", "Shadipur Metro", "Baljit Nagar", "Anand Parbat Industrial", "Dev Nagar Karol Bagh", "Pusa Institute Campus", "Prasad Nagar", "Bapa Nagar", "Tank Road Market", "Jhandewalan Temple", "Motia Khan", "Karol Bagh Pusa Rd", "Naraina Vihar", "Naraina Industrial Area 1", "Inderpuri"],
        8: ["Chandni Chowk Gurudwara", "Red Fort Enclave", "Jama Masjid Ward", "Dariba Kalan", "Chawri Bazar", "Ballimaran", "Fatehpuri", "Kashmere Gate ISBT", "Mori Gate", "Sadar Bazar Bara Tooti", "Sadar Bazar Qutab Rd", "Paharganj Main Bazaar", "Aram Bagh", "Qadam Sharif", "Nabi Karim", "Idgah Enclave", "Delhi Gate LNJP Area", "Asaf Ali Road", "Turkman Gate", "Ajmeri Gate", "Lahori Gate"],
        9: ["Keshav Puram Block A", "Keshav Puram Block C", "Lawrence Road Industrial", "Tri Nagar Main", "Tri Nagar Totaram Bazar", "Rampura", "Shanti Nagar Tri Nagar", "Ashok Vihar Phase 1", "Ashok Vihar Phase 2", "Ashok Vihar Phase 3", "Wazirpur Industrial Area", "Wazirpur Village", "Shalimar Bagh North", "Shalimar Bagh South", "Shalimar Bagh West", "Haiderpur", "Badli Village", "Shakurpur JJ Colony", "Britannia Chowk", "Kohat Enclave North", "Kanhaiya Nagar"],
        10: ["Narela Mandi", "Narela Sector A-6", "Narela Industrial Complex", "Alipur Block", "Bakhtawarpur", "Holambi Kalan", "Holambi Khurd", "Bawana Industrial Area", "Bawana Village", "Pooth Khurd", "Shahbad Dairy", "Samaypur Badli", "Libaspur", "Siraspur", "Khera Kalan", "Singhu Border", "Bhorgarh Industrial", "Lampur Border", "Bankner", "Narela DSIIDC", "Tikri Khurd"],
        11: ["Seelampur Metro", "Seelampur Market", "Welcome Colony", "Jafrabad Main", "Maujpur Chowk", "Babarpur East", "Babarpur West", "Yamuna Vihar Block B", "Yamuna Vihar Block C", "Bhajanpura", "Gokulpuri", "Harsh Vihar", "Nand Nagri Block A", "Nand Nagri Block C", "Sunder Nagri", "Dilshad Garden Pocket A", "Dilshad Colony", "Tahirpur Leprosy Mission", "GTB Hospital Enclave", "New Seemapuri"],
        12: ["Shahdara Old Court", "Shahdara Railway Station", "Vivek Vihar Phase 1", "Vivek Vihar Phase 2", "Jhilmil Industrial Area", "Anand Vihar ISBT", "Karkardooma Courts", "Preet Vihar Main", "Nirman Vihar", "Laxmi Nagar Vikas Marg", "Laxmi Nagar Metro", "Shakarpur", "Pandav Nagar", "Patparganj Industrial Area", "Mayur Vihar Phase 1", "Mayur Vihar Phase 2", "Mayur Vihar Pocket 1", "Trilokpuri Block 15", "Trilokpuri Block 27", "Kalyanpuri"],
    }
}


def generate_city_data(city_key: str = "chennai", seed: int = 42) -> Dict[str, Any]:
    """
    Generates synthetic spatial datasets for a single specified city.
    """
    city_cfg = config.get_city_config(city_key)
    city_name = city_cfg["city_name"]
    state_name = city_cfg["state_name"]
    state_code = city_cfg["state_code"]
    admin_count = city_cfg["admin_count"]
    crs_proj = city_cfg["crs_proj"]
    bbox = city_cfg["bbox"]
    center = city_cfg["center"]
    zones = city_cfg["zones"]

    print(f"\n---> Generating synthetic datasets for {city_name}, {state_name} ({admin_count} Wards)...")
    np.random.seed(seed)

    # 1. Distribute wards among zones
    num_zones = len(zones)
    base_wards_per_zone = admin_count // num_zones
    extra_wards = admin_count % num_zones

    ward_records = []
    pop_records = []
    ward_points = []
    ward_counter = 1

    # Compute zone center coordinates dispersed around city center
    zone_centers = []
    for i, z in enumerate(zones):
        angle = (2 * np.pi * i) / num_zones
        # Span ~40% of bounding box radius
        dlat = ((bbox["max_lat"] - bbox["min_lat"]) * 0.35) * np.sin(angle)
        dlon = ((bbox["max_lon"] - bbox["min_lon"]) * 0.35) * np.cos(angle)
        zlat = center[0] + dlat
        zlon = center[1] + dlon
        zone_centers.append((zlat, zlon))

    city_names_pool = CITY_WARD_NAMES.get(city_key, {})

    for idx, z in enumerate(zones):
        zid = z["zone_id"]
        zname = z["zone_name"]
        num_w = base_wards_per_zone + (1 if idx < extra_wards else 0)
        zlat, zlon = zone_centers[idx]

        # Density factor: central zones are denser
        dfactor = 1.4 if "Central" in zname or idx in [0, 1] else (0.85 if "North" in zname or "East" in zname else 1.0)
        zone_locality_names = city_names_pool.get(zid, [])

        for w in range(num_w):
            wid = ward_counter
            # Assign authentic locality name if available in the curated pool
            if w < len(zone_locality_names):
                locality = zone_locality_names[w]
            else:
                locality = f"{zname} Sector {w + 1}"
            
            wname = f"{locality} (Ward {wid:03d})"
            ward_counter += 1

            # Jitter within zone
            lat_jitter = np.random.normal(0, (bbox["max_lat"] - bbox["min_lat"]) * 0.08)
            lon_jitter = np.random.normal(0, (bbox["max_lon"] - bbox["min_lon"]) * 0.08)
            lat = np.clip(zlat + lat_jitter, bbox["min_lat"] + 0.01, bbox["max_lat"] - 0.01)
            lon = np.clip(zlon + lon_jitter, bbox["min_lon"] + 0.01, bbox["max_lon"] - 0.01)

            ward_points.append(Point(lon, lat))

            # Realistic ward population based on city scale
            city_avg_ward_pop = city_cfg["approx_population"] // admin_count
            base_pop = int(np.random.normal(city_avg_ward_pop, city_avg_ward_pop * 0.15))
            pop = int(base_pop * dfactor)
            pop = max(12000, min(95000, pop))

            elderly = int(pop * np.random.uniform(0.08, 0.13))
            children = int(pop * np.random.uniform(0.14, 0.20))
            working_age = pop - elderly - children
            households = int(round(pop / np.random.uniform(3.7, 4.3)))

            composite_id = f"IND_{state_code}_{city_key[:3].upper()}_{wid:03d}"

            pop_records.append({
                "Composite_ID": composite_id,
                "Country": "India",
                "State": state_name,
                "State_Code": state_code,
                "City": city_name,
                "City_Key": city_key,
                "Administrative_Area_ID": wid,
                "Administrative_Area_Name": wname,
                "Ward_ID": wid,
                "Ward_Name": wname,
                "Zone": zname,
                "Zone_ID": zid,
                "Population": pop,
                "Elderly": elderly,
                "Children": children,
                "Working_Age": working_age,
                "Households": households,
                "Data_Provenance": f"SYNTHETIC DEVELOPMENT DATA (Calibrated to {city_cfg['admin_body']})",
                "Data_Year": 2024,
            })

            ward_records.append({
                "Composite_ID": composite_id,
                "Country": "India",
                "State": state_name,
                "State_Code": state_code,
                "City": city_name,
                "City_Key": city_key,
                "Administrative_Area_ID": wid,
                "Administrative_Area_Name": wname,
                "Ward_ID": wid,
                "Ward_Name": wname,
                "Zone": zname,
                "Zone_ID": zid,
                "Centroid_Lat": round(lat, 6),
                "Centroid_Lon": round(lon, 6),
                "Data_Provenance": f"SYNTHETIC DEVELOPMENT DATA (Calibrated to {city_cfg['admin_body']})",
            })

    # Create contiguous Voronoi polygons
    city_box = box(bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])
    pts_multipoint = gpd.GeoSeries(ward_points).unary_union
    voronoi_polys = voronoi_diagram(pts_multipoint, envelope=city_box)

    voronoi_geoms = list(voronoi_polys.geoms)
    assigned_geoms = [None] * len(ward_points)

    for poly in voronoi_geoms:
        clipped = poly.intersection(city_box)
        if clipped.is_empty:
            continue
        dists = [pt.distance(clipped.centroid) for pt in ward_points]
        best_idx = np.argmin(dists)
        assigned_geoms[best_idx] = clipped

    for i in range(len(assigned_geoms)):
        if assigned_geoms[i] is None or assigned_geoms[i].is_empty:
            assigned_geoms[i] = ward_points[i].buffer(0.015)

    wards_gdf = gpd.GeoDataFrame(ward_records, geometry=assigned_geoms, crs=config.CRS_GEO)

    # Compute area using city-specific projected metric CRS
    wards_utm = wards_gdf.to_crs(crs_proj)
    wards_gdf["Area_km2"] = (wards_utm.geometry.area / 1e6).round(3)

    pop_df = pd.DataFrame(pop_records)
    pop_df["Area_km2"] = wards_gdf["Area_km2"].values
    pop_df["Population_Density"] = (pop_df["Population"] / pop_df["Area_km2"].replace(0, 0.01)).round(1)

    # 2. Generate Healthcare Facilities
    fac_records = []
    fac_counter = 1

    # A. Real Landmark Hospitals
    landmarks = LANDMARK_FACILITIES.get(city_key, LANDMARK_FACILITIES["chennai"])
    for name, lat, lon, ftype, beds, docs, ownership in landmarks:
        fid = f"FAC_{city_key[:3].upper()}_{fac_counter:03d}"
        fac_counter += 1
        fac_records.append({
            "Facility_ID": fid,
            "Facility_Name": name,
            "City": city_name,
            "City_Key": city_key,
            "State": state_name,
            "Latitude": round(lat, 6),
            "Longitude": round(lon, 6),
            "Facility_Type": ftype,
            "Beds": beds,
            "Doctors": docs,
            "Ownership": ownership,
            "Data_Provenance": "SYNTHETIC DEVELOPMENT DATA (Landmark Calibrated)",
            "Data_Year": 2024,
        })

    # B. Community Health Centres (CHCs) with authentic neighborhood tags
    num_chcs = admin_count // 5
    for i in range(num_chcs):
        fid = f"FAC_{city_key[:3].upper()}_{fac_counter:03d}"
        fac_counter += 1
        ref_idx = np.random.randint(0, len(ward_points))
        ref_pt = ward_points[ref_idx]
        ref_wname = ward_records[ref_idx]["Ward_Name"].split(" (")[0]
        lat = ref_pt.y + np.random.normal(0, 0.005)
        lon = ref_pt.x + np.random.normal(0, 0.005)
        beds = int(np.random.randint(25, 55))
        docs = int(np.random.randint(5, 10))
        ownership = "Public" if np.random.rand() > 0.3 else "Private"

        fac_records.append({
            "Facility_ID": fid,
            "Facility_Name": f"{ref_wname} Community Health Centre",
            "City": city_name,
            "City_Key": city_key,
            "State": state_name,
            "Latitude": round(lat, 6),
            "Longitude": round(lon, 6),
            "Facility_Type": "CHC",
            "Beds": beds,
            "Doctors": docs,
            "Ownership": ownership,
            "Data_Provenance": "SYNTHETIC DEVELOPMENT DATA",
            "Data_Year": 2024,
        })

    # C. Primary & Urban Primary Health Centres (UPHC/PHC)
    num_uphcs = int(admin_count * 0.45)
    for i in range(num_uphcs):
        fid = f"FAC_{city_key[:3].upper()}_{fac_counter:03d}"
        fac_counter += 1
        ref_idx = np.random.randint(0, len(ward_points))
        ref_pt = ward_points[ref_idx]
        ref_wname = ward_records[ref_idx]["Ward_Name"].split(" (")[0]
        lat = ref_pt.y + np.random.normal(0, 0.004)
        lon = ref_pt.x + np.random.normal(0, 0.004)
        ftype = "UPHC" if i < int(num_uphcs * 0.7) else "PHC"
        beds = int(np.random.randint(6, 16))
        docs = int(np.random.randint(2, 5))

        fac_records.append({
            "Facility_ID": fid,
            "Facility_Name": f"{ref_wname} Urban Primary Health Centre" if ftype == "UPHC" else f"{ref_wname} Primary Health Centre",
            "City": city_name,
            "City_Key": city_key,
            "State": state_name,
            "Latitude": round(lat, 6),
            "Longitude": round(lon, 6),
            "Facility_Type": ftype,
            "Beds": beds,
            "Doctors": docs,
            "Ownership": "Public",
            "Data_Provenance": "SYNTHETIC DEVELOPMENT DATA",
            "Data_Year": 2024,
        })

    # D. Private Clinics & Nursing Homes
    num_pvt = admin_count // 6
    for i in range(num_pvt):
        fid = f"FAC_{city_key[:3].upper()}_{fac_counter:03d}"
        fac_counter += 1
        ref_idx = np.random.randint(0, len(ward_points))
        ref_pt = ward_points[ref_idx]
        ref_wname = ward_records[ref_idx]["Ward_Name"].split(" (")[0]
        lat = ref_pt.y + np.random.normal(0, 0.004)
        lon = ref_pt.x + np.random.normal(0, 0.004)
        beds = int(np.random.randint(10, 35))
        docs = int(np.random.randint(3, 8))

        fac_records.append({
            "Facility_ID": fid,
            "Facility_Name": f"{ref_wname} Medicare & Nursing Home",
            "City": city_name,
            "City_Key": city_key,
            "State": state_name,
            "Latitude": round(lat, 6),
            "Longitude": round(lon, 6),
            "Facility_Type": "Private Clinic",
            "Beds": beds,
            "Doctors": docs,
            "Ownership": "Private",
            "Data_Provenance": "SYNTHETIC DEVELOPMENT DATA",
            "Data_Year": 2024,
        })

    fac_df = pd.DataFrame(fac_records)

    # Save to city paths
    paths = config.get_city_data_paths(city_key)
    wards_gdf.to_file(paths["sample_wards_geojson"], driver="GeoJSON")
    pop_df.to_csv(paths["sample_pop_csv"], index=False)
    fac_df.to_csv(paths["sample_fac_csv"], index=False)

    print(f"  [OK] Saved {len(wards_gdf)} wards to {paths['sample_wards_geojson'].name}")
    print(f"  [OK] Saved population ({pop_df['Population'].sum():,} pop) to {paths['sample_pop_csv'].name}")
    print(f"  [OK] Saved {len(fac_df)} facilities to {paths['sample_fac_csv'].name}")

    return {
        "city_key": city_key,
        "city_name": city_name,
        "wards_count": len(wards_gdf),
        "facilities_count": len(fac_df),
        "total_population": int(pop_df["Population"].sum()),
        "total_beds": int(fac_df["Beds"].sum()),
    }


def generate_all_cities_sample_data():
    """Generates development spatial data for all active cities in the registry."""
    print("=" * 70)
    print("CRADLE: GENERATING MULTI-CITY DEVELOPMENT DATA (5 CITIES)")
    print("=" * 70)
    summary = []
    for city_key, city_cfg in config.SUPPORTED_CITIES.items():
        if city_cfg.get("is_active", False):
            res = generate_city_data(city_key)
            summary.append(res)
    print("\n" + "=" * 70)
    print(f"MULTI-CITY GENERATION COMPLETED: {len(summary)} cities ready.")
    for s in summary:
        print(f"  * {s['city_name']}: {s['wards_count']} Wards | {s['facilities_count']} Facilities | {s['total_population']:,} Population | {s['total_beds']:,} Beds")
    print("=" * 70)
    return summary


if __name__ == "__main__":
    generate_all_cities_sample_data()
