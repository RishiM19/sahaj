// Matches backend/app/seed.py - same phone numbers, same story.
export interface Persona {
  phone: string;
  name: string;
  role: string;
  color: string;
  seedMessage: string;
}

export const PERSONAS: Persona[] = [
  {
    phone: "+919820011111",
    name: "Rajesh",
    role: "Swiggy driver · Mumbai",
    color: "#4f8cff",
    seedMessage: "Ek loan app mila hai friend ne share kiya. QuickCash24 se ₹15,000 chahiye. Is this safe?",
  },
  {
    phone: "+919820022222",
    name: "Priya",
    role: "Schoolteacher · Thane",
    color: "#8b6bff",
    seedMessage: "I want to start a small SIP but someone tried to sell me a ULIP instead. What should I actually do?",
  },
  {
    phone: "+919820033333",
    name: "Kisan",
    role: "Paddy farmer · Karnataka",
    color: "#2ecc8f",
    seedMessage: "Naanu Kisan Credit Card ge apply madabeku, aadre form English nalli ide.",
  },
  {
    phone: "+919820044444",
    name: "Divya",
    role: "Writer · Pune",
    color: "#f0a020",
    seedMessage: "I need to file a Section 80DD disability claim but I can't read the form fields.",
  },
];
