# Extract (v1 rules — mirrored in backend/app/services/understanding.py)
Return JSON only with this schema:
{origin, destination, quantity, equipment, weight_kg, mode, incoterm, service, missing[], confidence{}}
Rules:
- Only fill fields explicitly stated. Never guess weight, dims, or mode.
- "5 cartons from Guangzhou to Lagos" -> quantity=5 cartons, origin/dest set, weight=null, missing=[weight, dimensions, mode, cargo].
- "20ft China to Lagos" -> equipment=20ft, missing includes weight/pickup/incoterm.
