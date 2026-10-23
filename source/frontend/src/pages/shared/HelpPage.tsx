// Guides for each role, written as short question-and-answer sections.
import { useAuth } from "../../context/AuthContext";
import type { Role } from "../../types";

interface Topic {
  title: string;
  steps: string[];
}

const GUIDES: Record<Role, Topic[]> = {
  doctor: [
    {
      title: "How does my day work?",
      steps: [
        "The Dashboard shows who is waiting, who is being examined, and what is coming up. It refreshes by itself.",
        "Patients appear in the Appointments queue when they are checked in. You are notified when somebody new arrives.",
        "You can only examine one patient at a time. Finish or return the current patient before starting another.",
      ],
    },
    {
      title: "How do I examine a patient?",
      steps: [
        "In Appointments, choose a room (optional) and press Start examination. This creates the invoice with the default consultation fee.",
        "Enter the diagnosis and notes, add medicines with their quantity and price, and adjust the consultation fee if needed.",
        "Optionally book a follow-up visit, then press Finish examination and send invoice.",
        "Started by mistake? Use Return to queue to put the patient back.",
      ],
    },
    {
      title: "Where are prescriptions and payments?",
      steps: [
        "Prescriptions lists everything you have issued. History shows paid visits with their prescriptions.",
        "Invoice shows what patients owe. You or your nurse can mark an invoice paid after the examination is finished.",
        "If an examined session has no invoice, create it from the top of the Invoice page.",
      ],
    },
    {
      title: "What about appointment requests?",
      steps: [
        "Notifications lists requests from the public booking page. Approve to create the patient and appointment, or disapprove with a reason. The patient is emailed either way.",
      ],
    },
  ],
  nurse: [
    {
      title: "How do I handle requests?",
      steps: [
        "Open Notifications. Approve a request to add the patient and the appointment; you can change the time and pick a room first.",
        "A warning appears when the requested time is already booked.",
        "To disapprove, write a short reason. It is emailed to the patient.",
      ],
    },
    {
      title: "How do I check patients in?",
      steps: [
        "In Appointments, press Check in next to a booked patient when they arrive. They join the waiting queue and your doctor is notified.",
        "Use New appointment for walk-ins. Tick Check the patient in now to add them to the queue straight away.",
        "Use Reschedule or Cancel when plans change. Cancelling frees the time for another booking.",
      ],
    },
    {
      title: "How do I take payment?",
      steps: [
        "Open Invoice. When the doctor has finished the examination, press Mark as paid after the patient pays. The visit moves to History.",
        "Sessions without an invoice are listed at the top of the page. Create the invoice there.",
      ],
    },
    {
      title: "What can I do with rooms and patients?",
      steps: [
        "The Rooms section of Appointments lets you set a room to Available, Occupied or Maintenance.",
        "Patients lets you search, add, edit and open records. A patient with appointments on record cannot be deleted.",
      ],
    },
  ],
  admin: [
    {
      title: "How do I manage staff?",
      steps: [
        "In Users, press Add user to create a doctor, nurse or administrator. A nurse must be assigned to the doctor they support.",
        "Edit changes a name, email, specialization or assigned doctor. Reset password sets a new password. Deactivate blocks sign-in without deleting history.",
        "For doctors, press Schedule to set weekly working hours. The public booking page builds its open times from them.",
      ],
    },
    {
      title: "How do I manage rooms and settings?",
      steps: [
        "Rooms lets you add, rename, set status, and delete rooms. A room used in past appointments cannot be deleted; set it to Maintenance instead.",
        "Clinic Settings holds the clinic name and address, the default consultation fee, slot length, booking window, and the switch that opens or closes online booking.",
      ],
    },
    {
      title: "Where are reports and the activity log?",
      steps: [
        "Reports summarizes appointments and revenue for a date range, and can be downloaded as CSV.",
        "Audit Logs shows who did what and when. Search by text, filter by action, and download the current page.",
      ],
    },
  ],
};

const COMMON: Topic[] = [
  {
    title: "How do I change my password or photo?",
    steps: ["Open Settings to change your password. Open Profile to change your name, email and photo."],
  },
  {
    title: "I was signed out or something looks wrong.",
    steps: [
      "Sessions expire after a while. Sign in again from the home page.",
      "If a page says it cannot reach the server, check that the backend is running and refresh.",
      "Ask an administrator if your account was deactivated.",
    ],
  },
];

export default function HelpPage() {
  const { user } = useAuth();
  const role = user?.role ?? "doctor";
  const topics = [...GUIDES[role], ...COMMON];

  return (
    <section className="max-w-3xl">
      <h1 className="text-2xl font-semibold">Help</h1>
      <p className="mt-1 text-slate-600">Short guides for your role. Open a topic to read it.</p>
      <div className="mt-6 space-y-3">
        {topics.map((topic, index) => (
          <details key={topic.title} open={index === 0} className="rounded-xl border border-slate-200 bg-white p-4">
            <summary className="cursor-pointer font-medium">{topic.title}</summary>
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-700">
              {topic.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </details>
        ))}
      </div>
    </section>
  );
}