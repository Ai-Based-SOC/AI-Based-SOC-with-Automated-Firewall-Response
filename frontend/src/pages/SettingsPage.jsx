import { useState } from "react";
import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import {
  changePasswordApi,
  updateProfileApi,
} from "../services/api";

export default function SettingsPage({ profile, onLogout }) {
  const [fullName, setFullName] = useState(profile?.full_name || "");
  const [email, setEmail] = useState(profile?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");

  async function updateProfile(event) {
    event.preventDefault();

    try {
      await updateProfileApi({
        full_name: fullName,
        email,
      });

      setMessage("Profile updated successfully.");
    } catch {
      setMessage("Profile update failed.");
    }
  }

  async function updatePassword(event) {
    event.preventDefault();

    try {
      await changePasswordApi({
        current_password: currentPassword,
        new_password: newPassword,
      });

      setCurrentPassword("");
      setNewPassword("");
      setMessage("Password changed successfully.");
    } catch {
      setMessage("Password change failed.");
    }
  }

  return (
    <PageShell title="Settings" profile={profile} onLogout={onLogout}>
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-4 xl:grid-cols-2">
        <Panel title="Profile">
          <form onSubmit={updateProfile} className="space-y-4">
            <label className="block text-sm text-slate-400">
              Full Name
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm text-white"
              />
            </label>

            <label className="block text-sm text-slate-400">
              Email
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1 w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm text-white"
              />
            </label>

            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm">
              Update Profile
            </button>
          </form>
        </Panel>

        <Panel title="Change Password">
          <form onSubmit={updatePassword} className="space-y-4">
            <input
              type="password"
              placeholder="Current password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              className="w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
            />

            <input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              className="w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
            />

            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm">
              Change Password
            </button>
          </form>
        </Panel>

        {message && (
          <div className="xl:col-span-2 rounded-lg border border-cyan-900 bg-cyan-500/10 p-3 text-sm text-cyan-200">
            {message}
          </div>
        )}
      </div>
    </PageShell>
  );
}