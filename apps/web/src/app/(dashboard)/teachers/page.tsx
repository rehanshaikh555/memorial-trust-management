"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  AlertCircle,
  Eye,
  GraduationCap,
  Mail,
  Phone,
  Plus,
  Search,
  Users,
} from "lucide-react";
import { motion } from "framer-motion";

import {
  useCreateTeacher,
  useTeachers,
} from "@/hooks/use-teachers";
import {
  useSchoolList,
} from "@/hooks/use-academic-structure";
import {
  Button,
} from "@/components/ui/button";
import {
  Input,
} from "@/components/ui/input";
import {
  Badge,
} from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Label,
} from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Textarea,
} from "@/components/ui/textarea";

function teacherName(teacher: {
  first_name: string;
  middle_name: string | null;
  last_name: string | null;
}) {
  return [
    teacher.first_name,
    teacher.middle_name,
    teacher.last_name,
  ]
    .filter(Boolean)
    .join(" ");
}

function statusClass(status: string) {
  switch (status) {
    case "ACTIVE":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";
    case "SUBMITTED":
      return "border-blue-200 bg-blue-50 text-blue-700";
    case "READY_FOR_APPROVAL":
      return "border-violet-200 bg-violet-50 text-violet-700";
    case "APPLICATION_DRAFT":
      return "border-amber-200 bg-amber-50 text-amber-700";
    case "INACTIVE":
    case "DEACTIVATED":
      return "border-slate-200 bg-slate-100 text-slate-600";
    default:
      return "border-slate-200 bg-slate-50 text-slate-600";
  }
}

export default function TeachersPage() {
  const [search, setSearch] = useState("");
  const [schoolFilter, setSchoolFilter] = useState("ALL");
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [dialogOpen, setDialogOpen] = useState(false);

  const [schoolId, setSchoolId] = useState("");
  const [teacherId, setTeacherId] = useState("");
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [qualification, setQualification] = useState("");

  const teachers = useTeachers({
    schoolId:
      schoolFilter === "ALL"
        ? undefined
        : schoolFilter,
    includeInactive: activeFilter !== "ACTIVE",
  });

  const schools = useSchoolList();
  const createTeacher = useCreateTeacher();

  const filteredTeachers = useMemo(() => {
    const query = search.trim().toLowerCase();

    let result = teachers.data ?? [];

    if (activeFilter === "ACTIVE") {
      result = result.filter(
        (teacher) =>
          teacher.is_active &&
          teacher.status === "ACTIVE",
      );
    }

    if (activeFilter === "INACTIVE") {
      result = result.filter(
        (teacher) =>
          !teacher.is_active ||
          teacher.status !== "ACTIVE",
      );
    }

    if (!query) {
      return result;
    }

    return result.filter((teacher) =>
      [
        teacher.teacher_id,
        teacherName(teacher),
        teacher.email,
        teacher.phone,
        teacher.qualification,
        teacher.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query),
    );
  }, [
    teachers.data,
    search,
    activeFilter,
  ]);

  const resetForm = () => {
    setSchoolId("");
    setTeacherId("");
    setFirstName("");
    setMiddleName("");
    setLastName("");
    setDateOfBirth("");
    setGender("");
    setPhone("");
    setEmail("");
    setAddress("");
    setQualification("");
  };

  const handleCreate = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!schoolId || !teacherId || !firstName.trim()) {
      return;
    }

    try {
      await createTeacher.mutateAsync({
        school_id: schoolId,
        teacher_id: teacherId.trim(),
        first_name: firstName.trim(),
        middle_name:
          middleName.trim() || null,
        last_name:
          lastName.trim() || null,
        date_of_birth:
          dateOfBirth || null,
        gender: gender || null,
        phone: phone.trim() || null,
        email: email.trim() || null,
        address: address.trim() || null,
        qualification:
          qualification.trim() || null,
      });

      resetForm();
      setDialogOpen(false);
    } catch {
      // The mutation error is rendered below.
    }
  };

  return (
    <div className="mx-auto max-w-[1600px]">
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#27348B]/60">
            Staff management
          </p>

          <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-900">
            Teachers
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Manage teaching staff, approval status,
            school access and assignments.
          </p>
        </div>

        <Dialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
        >
          <DialogTrigger>
            <Button className="rounded-xl bg-[#27348B] shadow-lg shadow-[#27348B]/20 hover:bg-[#202c78]">
              <Plus className="mr-2 size-4" />
              Add teacher
            </Button>
          </DialogTrigger>

          <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                Add teacher
              </DialogTitle>

              <DialogDescription>
                Create a new teacher application
                for a school.
              </DialogDescription>
            </DialogHeader>

            <form
              onSubmit={handleCreate}
              className="space-y-5"
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label>School</Label>

                  <Select
                    value={schoolId}
                    onValueChange={(value) => setSchoolId(value ?? `)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select school" />
                    </SelectTrigger>

                    <SelectContent>
                      {(schools.data ?? [])
                        .filter(
                          (school) =>
                            school.is_active,
                        )
                        .map((school) => (
                          <SelectItem
                            key={school.id}
                            value={school.id}
                          >
                            {school.name} ({school.code})
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="teacher-id">
                    Teacher ID
                  </Label>

                  <Input
                    id="teacher-id"
                    value={teacherId}
                    onChange={(event) =>
                      setTeacherId(
                        event.target.value,
                      )
                    }
                    placeholder="TCH-001"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="first-name">
                    First name
                  </Label>

                  <Input
                    id="first-name"
                    value={firstName}
                    onChange={(event) =>
                      setFirstName(
                        event.target.value,
                      )
                    }
                    placeholder="First name"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="middle-name">
                    Middle name
                  </Label>

                  <Input
                    id="middle-name"
                    value={middleName}
                    onChange={(event) =>
                      setMiddleName(
                        event.target.value,
                      )
                    }
                    placeholder="Middle name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="last-name">
                    Last name
                  </Label>

                  <Input
                    id="last-name"
                    value={lastName}
                    onChange={(event) =>
                      setLastName(
                        event.target.value,
                      )
                    }
                    placeholder="Last name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="date-of-birth">
                    Date of birth
                  </Label>

                  <Input
                    id="date-of-birth"
                    type="date"
                    value={dateOfBirth}
                    onChange={(event) =>
                      setDateOfBirth(
                        event.target.value,
                      )
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Gender</Label>

                  <Select
                    value={gender}
                    onValueChange={(value) => setGender(value ?? `)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>

                    <SelectContent>
                      <SelectItem value="MALE">
                        Male
                      </SelectItem>
                      <SelectItem value="FEMALE">
                        Female
                      </SelectItem>
                      <SelectItem value="OTHER">
                        Other
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">
                    Phone
                  </Label>

                  <Input
                    id="phone"
                    value={phone}
                    onChange={(event) =>
                      setPhone(
                        event.target.value,
                      )
                    }
                    placeholder="+91..."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">
                    Email
                  </Label>

                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(
                        event.target.value,
                      )
                    }
                    placeholder="teacher@example.com"
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="qualification">
                    Qualification
                  </Label>

                  <Input
                    id="qualification"
                    value={qualification}
                    onChange={(event) =>
                      setQualification(
                        event.target.value,
                      )
                    }
                    placeholder="B.Ed, M.Ed, B.A..."
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="address">
                    Address
                  </Label>

                  <Textarea
                    id="address"
                    value={address}
                    onChange={(event) =>
                      setAddress(
                        event.target.value,
                      )
                    }
                    placeholder="Residential address"
                    rows={3}
                  />
                </div>
              </div>

              {createTeacher.isError && (
                <div className="rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">
                  {createTeacher.error instanceof Error
                    ? createTeacher.error.message
                    : "Unable to create teacher."}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-xl"
                  onClick={() =>
                    setDialogOpen(false)
                  }
                >
                  Cancel
                </Button>

                <Button
                  type="submit"
                  disabled={
                    createTeacher.isPending ||
                    !schoolId ||
                    !teacherId ||
                    !firstName.trim()
                  }
                  className="rounded-xl bg-[#27348B] hover:bg-[#202c78]"
                >
                  {createTeacher.isPending
                    ? "Creating..."
                    : "Create teacher"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="mb-5 rounded-3xl border border-white/50 bg-white/70 p-4 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="relative w-full xl:max-w-xl">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

            <Input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search by teacher ID, name, email, phone or qualification..."
              className="h-11 rounded-xl border-slate-200 bg-white/80 pl-10"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Select
              value={schoolFilter}
              onValueChange={(value) => setSchoolFilter(value ?? `ALL`)}
            >
              <SelectTrigger className="h-11 min-w-[190px] rounded-xl bg-white/80">
                <SelectValue placeholder="All schools" />
              </SelectTrigger>

              <SelectContent>
                <SelectItem value="ALL">
                  All schools
                </SelectItem>

                {(schools.data ?? [])
                  .filter(
                    (school) =>
                      school.is_active,
                  )
                  .map((school) => (
                    <SelectItem
                      key={school.id}
                      value={school.id}
                    >
                      {school.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>

            <Select
              value={activeFilter}
              onValueChange={(value) => setActiveFilter(value ?? `ALL`)}
            >
              <SelectTrigger className="h-11 min-w-[170px] rounded-xl bg-white/80">
                <SelectValue />
              </SelectTrigger>

              <SelectContent>
                <SelectItem value="ALL">
                  All teachers
                </SelectItem>
                <SelectItem value="ACTIVE">
                  Active only
                </SelectItem>
                <SelectItem value="INACTIVE">
                  Inactive / pending
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
          <Users className="size-4 text-[#27348B]" />
          <span>
            {filteredTeachers.length} visible teachers
          </span>
        </div>
      </div>

      {teachers.isLoading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map(
            (_, index) => (
              <div
                key={index}
                className="h-52 animate-pulse rounded-3xl border border-white/50 bg-white/70"
              />
            ),
          )}
        </div>
      )}

      {teachers.isError && (
        <div className="rounded-3xl border border-red-100 bg-red-50 p-8 text-center">
          <AlertCircle className="mx-auto size-8 text-red-500" />

          <p className="mt-3 font-bold text-red-700">
            Unable to load teachers
          </p>

          <p className="mt-1 text-sm text-red-600">
            {teachers.error instanceof Error
              ? teachers.error.message
              : "The API request failed."}
          </p>
        </div>
      )}

      {!teachers.isLoading &&
        !teachers.isError &&
        filteredTeachers.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-white/60 p-16 text-center backdrop-blur-xl">
            <GraduationCap className="mx-auto size-10 text-[#27348B]/40" />

            <p className="mt-4 font-bold text-slate-800">
              No teachers found
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Try another filter or create a new
              teacher record.
            </p>
          </div>
        )}

      {!teachers.isLoading &&
        !teachers.isError &&
        filteredTeachers.length > 0 && (
          <div className="overflow-hidden rounded-3xl border border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1050px]">
                <thead>
                  <tr className="border-b border-slate-100 bg-white/60 text-left">
                    <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Teacher
                    </th>

                    <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Teacher ID
                    </th>

                    <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Status
                    </th>

                    <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Contact
                    </th>

                    <th className="px-5 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Qualification
                    </th>

                    <th className="px-5 py-4 text-right text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {filteredTeachers.map(
                    (teacher, index) => (
                      <motion.tr
                        key={teacher.id}
                        initial={{
                          opacity: 0,
                        }}
                        animate={{
                          opacity: 1,
                        }}
                        transition={{
                          delay:
                            index * 0.025,
                        }}
                        className="border-b border-slate-100/80 transition hover:bg-white/70"
                      >
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[#27348B]/10 font-bold text-[#27348B]">
                              {teacher.first_name
                                .charAt(0)
                                .toUpperCase()}
                            </div>

                            <div>
                              <p className="font-semibold text-slate-800">
                                {teacherName(
                                  teacher,
                                )}
                              </p>

                              <p className="text-xs text-slate-400">
                                {teacher.email ||
                                  "No email"}
                              </p>
                            </div>
                          </div>
                        </td>

                        <td className="px-5 py-4 text-sm font-medium text-slate-600">
                          {teacher.teacher_id}
                        </td>

                        <td className="px-5 py-4">
                          <Badge
                            variant="outline"
                            className={`rounded-full ${statusClass(
                              teacher.status,
                            )}`}
                          >
                            {teacher.status}
                          </Badge>
                        </td>

                        <td className="px-5 py-4 text-sm text-slate-500">
                          <div className="space-y-1">
                            {teacher.phone && (
                              <div className="flex items-center gap-2">
                                <Phone className="size-3.5" />
                                <span>
                                  {teacher.phone}
                                </span>
                              </div>
                            )}

                            {teacher.email && (
                              <div className="flex items-center gap-2">
                                <Mail className="size-3.5" />
                                <span className="max-w-[220px] truncate">
                                  {teacher.email}
                                </span>
                              </div>
                            )}

                            {!teacher.phone &&
                              !teacher.email && (
                                <span>
                                  No contact
                                </span>
                              )}
                          </div>
                        </td>

                        <td className="px-5 py-4 text-sm text-slate-500">
                          <div className="flex items-center gap-2">
                            <GraduationCap className="size-4 text-[#27348B]/60" />
                            <span className="max-w-[180px] truncate">
                              {teacher.qualification ||
                                "Not provided"}
                            </span>
                          </div>
                        </td>

                        <td className="px-5 py-4 text-right">
                          <Link
                            href={`/teachers/${teacher.id}`}
                            className="inline-flex items-center gap-2 rounded-xl bg-[#27348B]/5 px-3 py-2 text-xs font-bold text-[#27348B] transition hover:bg-[#27348B]/10"
                          >
                            <Eye className="size-3.5" />
                            View
                          </Link>
                        </td>
                      </motion.tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
    </div>
  );
}


